"""Telegram bot service — polling-based bot that reuses the AI sales agent."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models import (
    TelegramConversation, TelegramMessage, Order, ConversationStatus,
)
from app.services import ai_agent

logger = logging.getLogger(__name__)

# ── Lazy import so the app starts even without python-telegram-bot installed ──

try:
    from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler, CallbackQueryHandler,
        ContextTypes, filters,
    )
    TELEGRAM_AVAILABLE = True
except ImportError:  # pragma: no cover
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot not installed — Telegram bot disabled")


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _get_or_create_conversation(
    db: AsyncSession,
    telegram_user_id: str,
    chat_id: str,
    username: Optional[str],
    full_name: Optional[str],
) -> TelegramConversation:
    result = await db.execute(
        select(TelegramConversation).where(
            TelegramConversation.telegram_user_id == telegram_user_id
        )
    )
    conv = result.scalar_one_or_none()

    if conv:
        conv.last_message_at = datetime.now(timezone.utc)
        if conv.status == ConversationStatus.EXPIRED.value:
            conv.status = ConversationStatus.ACTIVE.value
        if username and not conv.username:
            conv.username = username
        if full_name and not conv.full_name:
            conv.full_name = full_name
        await db.flush()
        return conv

    conv = TelegramConversation(
        telegram_user_id=telegram_user_id,
        chat_id=chat_id,
        username=username,
        full_name=full_name,
        status=ConversationStatus.ACTIVE.value,
    )
    db.add(conv)
    await db.flush()
    logger.info("New Telegram conversation: user_id=%s name=%s", telegram_user_id, full_name)
    return conv


async def _add_message(
    db: AsyncSession,
    conversation_id: int,
    sender: str,
    content: str,
    telegram_message_id: Optional[str] = None,
) -> TelegramMessage:
    msg = TelegramMessage(
        conversation_id=conversation_id,
        sender=sender,
        content=content,
        telegram_message_id=str(telegram_message_id) if telegram_message_id else None,
    )
    db.add(msg)
    await db.flush()
    return msg


async def _get_history(db: AsyncSession, conversation_id: int, limit: int = 20):
    """Return recent TelegramMessage rows as Message-like objects for the AI agent."""
    result = await db.execute(
        select(TelegramMessage)
        .where(TelegramMessage.conversation_id == conversation_id)
        .order_by(TelegramMessage.timestamp.desc())
        .limit(limit)
    )
    msgs = list(result.scalars().all())
    msgs.reverse()
    return msgs


# ── Handlers ──────────────────────────────────────────────────────────────────

async def _start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with a welcoming menu."""
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🛍 Посмотреть каталог", callback_data="catalog")],
        [InlineKeyboardButton("📞 Связаться с менеджером", callback_data="contact")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Ассаламу алейкум, {user.first_name}! 👋\n\n"
        "Добро пожаловать в *Bukhari Sales*.\n"
        "Я ваш AI-консультант по продажам. Напишите мне, что вас интересует, "
        "или выберите действие ниже:",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def _button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()

    if query.data == "catalog":
        async with async_session() as db:
            catalog = await ai_agent._build_product_catalog(db)
        # Trim to fit Telegram's 4096-char limit
        text = f"📦 *Наш каталог товаров:*\n\n{catalog}"
        if len(text) > 4000:
            text = text[:3997] + "..."
        await query.edit_message_text(text, parse_mode="Markdown")

    elif query.data == "contact":
        await query.edit_message_text(
            "Чтобы связаться с менеджером, напишите нам напрямую или оставьте свои контакты — "
            "мы перезвоним вам в ближайшее время! 📞"
        )


async def _message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle every incoming text message — run it through the AI agent."""
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    telegram_user_id = str(user.id)
    username = user.username
    full_name = " ".join(filter(None, [user.first_name, user.last_name]))
    text = update.message.text
    message_id = update.message.message_id

    async with async_session() as db:
        # Persist conversation & incoming message
        conv = await _get_or_create_conversation(
            db, telegram_user_id, chat_id, username, full_name
        )
        await _add_message(db, conv.id, "user", text, message_id)
        history = await _get_history(db, conv.id)

        # Generate AI reply (reuse existing agent — it reads from the same Product table)
        display_name = full_name or username or telegram_user_id
        ai_reply = await ai_agent.generate_response(
            db=db,
            user_message=text,
            conversation_history=history,
            username=display_name,
            conversation_id=None,
            instagram_user_id=f"tg:{telegram_user_id}",
            telegram_conversation_id=conv.id,
            telegram_user_id=telegram_user_id,
            channel="telegram",
        )

        # Persist bot reply
        await _add_message(db, conv.id, "bot", ai_reply)
        await db.commit()

    # Send reply (split if > 4096 chars)
    chunks = [ai_reply[i : i + 4096] for i in range(0, len(ai_reply), 4096)]
    for chunk in chunks:
        await update.message.reply_text(chunk)


async def _error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Telegram bot error: %s", context.error, exc_info=context.error)


# ── Bot lifecycle ─────────────────────────────────────────────────────────────

_application: Optional["Application"] = None  # type: ignore[type-arg]


async def start_bot(token: str) -> None:
    """Build and start the Telegram bot with polling (background task)."""
    global _application
    if not TELEGRAM_AVAILABLE:
        logger.warning("Skipping Telegram bot start — library not available")
        return

    if not token or token == "":
        logger.warning("Telegram bot token not set — skipping")
        return

    _application = (
        Application.builder()
        .token(token)
        .build()
    )

    _application.add_handler(CommandHandler("start", _start_handler))
    _application.add_handler(CallbackQueryHandler(_button_handler))
    _application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, _message_handler)
    )
    _application.add_error_handler(_error_handler)

    await _application.initialize()
    await _application.start()
    # Start polling in background — this does not block
    await _application.updater.start_polling(drop_pending_updates=True)
    logger.info("✅ Telegram bot started (polling)")


async def stop_bot() -> None:
    """Stop the Telegram bot gracefully."""
    global _application
    if _application is None:
        return
    try:
        await _application.updater.stop()
        await _application.stop()
        await _application.shutdown()
        logger.info("🛑 Telegram bot stopped")
    except Exception as e:
        logger.warning("Error stopping Telegram bot: %s", e)
    _application = None
