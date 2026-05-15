"""LangChain AI agent with tool-calling for sales consultation and order creation."""

import json
import logging
from collections import defaultdict
from typing import List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Product, AIConfig, Message, Order, TelegramMessage
from app.prompts.sales_agent import DEFAULT_SYSTEM_PROMPT, NO_PRODUCTS_MESSAGE

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Tool definition passed to OpenAI function-calling ────────────────────────

CREATE_ORDER_TOOL = {
    "type": "function",
    "function": {
        "name": "create_order",
        "description": (
            "Создать заказ на покупку, когда клиент явно подтвердил намерение купить товар "
            "и предоставил своё имя и контактные данные. "
            "Вызывайте эту функцию ТОЛЬКО тогда, когда у вас есть все три параметра."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "ID варианта товара из каталога (число в скобках рядом с ценой)",
                },
                "customer_name": {
                    "type": "string",
                    "description": "Имя клиента, которое он назвал",
                },
                "customer_contact": {
                    "type": "string",
                    "description": "Контактные данные клиента: номер телефона, email или ник в Instagram",
                },
                "notes": {
                    "type": "string",
                    "description": "Дополнительные пожелания клиента (необязательно)",
                    "default": "",
                },
            },
            "required": ["product_id", "customer_name", "customer_contact"],
        },
    },
}


# ── Internal helpers ─────────────────────────────────────────────────────────

async def _get_ai_config(db: AsyncSession) -> dict:
    result = await db.execute(select(AIConfig).limit(1))
    config = result.scalar_one_or_none()
    if config:
        return {
            "system_prompt": config.system_prompt,
            "temperature": config.temperature,
            "model_name": config.model_name,
            "max_tokens": config.max_tokens,
        }
    return {
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "temperature": 0.7,
        "model_name": "gpt-4o-mini",
        "max_tokens": 500,
    }


async def _build_product_catalog(db: AsyncSession) -> str:
    """Build a catalog grouped by category with variants listed per group."""
    result = await db.execute(select(Product))
    products = result.scalars().all()

    if not products:
        return NO_PRODUCTS_MESSAGE

    # Group by category (fall back to product name as category)
    groups: dict[str, list[Product]] = defaultdict(list)
    for p in products:
        key = p.category or p.name
        groups[key].append(p)

    parts: list[str] = []
    for cat_name, variants in groups.items():
        # Category header
        parts.append(f"## {cat_name}")

        # Shared description (from first product)
        cat_desc = next((v.description for v in variants if v.description), None)
        if cat_desc:
            parts.append(cat_desc.strip())

        parts.append("")
        parts.append("**Варианты и цены:**")
        for v in variants:
            label = v.variant_name or v.name
            stock = "✅" if v.in_stock else "❌ нет в наличии"
            parts.append(f"- {stock} **{label}** (ID товара: {v.id}): {v.price:,.0f} ₸")

        parts.append("")

    return "\n".join(parts)


async def _execute_create_order(
    db: AsyncSession,
    tool_args: dict,
    conversation_id: Optional[int],
    instagram_user_id: str,
    username: Optional[str],
    telegram_conversation_id: Optional[int] = None,
    telegram_user_id: Optional[str] = None,
    channel: str = "instagram",
) -> str:
    """Execute the create_order tool call and persist to DB."""
    product_id = tool_args["product_id"]
    customer_name = tool_args["customer_name"]
    customer_contact = tool_args["customer_contact"]
    notes = tool_args.get("notes", "")

    # Validate product exists
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        return f"Ошибка: товар с ID {product_id} не найден."

    order = Order(
        conversation_id=conversation_id,
        telegram_conversation_id=telegram_conversation_id,
        product_id=product.id,
        instagram_user_id=instagram_user_id if channel == "instagram" else None,
        telegram_user_id=telegram_user_id,
        username=username,
        customer_name=customer_name,
        customer_contact=customer_contact,
        notes=notes,
        channel=channel,
        status="confirmed",
    )
    db.add(order)
    await db.flush()
    await db.commit()

    variant = product.variant_name or product.name
    logger.info(
        "Order #%d created: user=%s product=%s (%s ₸) channel=%s",
        order.id, username, variant, product.price, channel,
    )
    return (
        f"Заказ #{order.id} успешно создан!\n"
        f"Товар: {variant} — {product.price:,.0f} ₸\n"
        f"Клиент: {customer_name}\n"
        f"Контакт: {customer_contact}"
    )


def _build_message_history(messages) -> list:
    lc_messages = []
    for msg in messages:
        if msg.sender == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.sender in ("bot", "operator"):
            lc_messages.append(AIMessage(content=msg.content))
    return lc_messages


# ── Main generate function ────────────────────────────────────────────────────

async def generate_response(
    db: AsyncSession,
    user_message: str,
    conversation_history,
    username: Optional[str] = None,
    conversation_id: Optional[int] = None,
    instagram_user_id: str = "unknown",
    telegram_conversation_id: Optional[int] = None,
    telegram_user_id: Optional[str] = None,
    channel: str = "instagram",
) -> str:
    """Generate a sales response, executing tool calls if the AI decides to create an order."""
    try:
        ai_config = await _get_ai_config(db)
        product_catalog = await _build_product_catalog(db)

        context_parts = []
        if username:
            context_parts.append(f"Имя клиента: {username}")
        context_parts.append(f"Сообщений в беседе: {len(conversation_history)}")
        conversation_context = "\n".join(context_parts) if context_parts else "Новая беседа"

        system_prompt = ai_config["system_prompt"].format(
            product_catalog=product_catalog,
            conversation_context=conversation_context,
        )

        llm = ChatOpenAI(
            model=ai_config["model_name"],
            temperature=ai_config["temperature"],
            max_tokens=ai_config["max_tokens"],
            api_key=settings.openai_api_key,
        )

        # Build message chain
        messages = [SystemMessage(content=system_prompt)]
        messages.extend(_build_message_history(conversation_history[-12:]))
        messages.append(HumanMessage(content=user_message))

        # First call — with tool available
        response = await llm.bind_tools([CREATE_ORDER_TOOL]).ainvoke(messages)

        # Check if the AI wants to call a tool
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            tool_args = tool_call["args"]
            logger.info("AI calling tool: %s with args: %s", tool_call["name"], tool_args)

            # Execute the order creation
            tool_result = await _execute_create_order(
                db=db,
                tool_args=tool_args,
                conversation_id=conversation_id,
                instagram_user_id=instagram_user_id,
                username=username,
                telegram_conversation_id=telegram_conversation_id,
                telegram_user_id=telegram_user_id,
                channel=channel,
            )

            # Second call — give the AI the tool result to form a natural reply
            messages.append(response)
            messages.append(ToolMessage(
                content=tool_result,
                tool_call_id=tool_call["id"],
            ))

            followup = await llm.ainvoke(messages)
            reply_text = followup.content.strip()
        else:
            reply_text = response.content.strip()

        logger.info("AI reply for %s: %s", username or "unknown", reply_text[:100])
        return reply_text

    except Exception as e:
        logger.error("AI generation failed: %s", e, exc_info=True)
        return (
            "Спасибо за сообщение! 😊 Небольшие технические трудности, "
            "но наш менеджер скоро свяжется с вами!"
        )
