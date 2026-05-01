"""Demo router — simulate Instagram DM conversations for testing."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import conversation as conv_service
from app.services import ai_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo", tags=["demo"])

DEMO_USER_ID = "demo_user_001"
DEMO_USERNAME = "Тестовый клиент"


class DemoChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class DemoChatResponse(BaseModel):
    user_message: str
    bot_reply: str
    conversation_id: int
    timestamp: str


@router.post("/chat", response_model=DemoChatResponse)
async def demo_chat(body: DemoChatRequest, db: AsyncSession = Depends(get_db)):
    """Simulate an Instagram DM conversation with the AI agent.

    This endpoint mimics the webhook flow without touching Instagram:
    1. Creates/finds a demo conversation
    2. Stores the user message
    3. Generates an AI response via LangChain
    4. Stores the bot reply
    5. Returns both messages
    """
    # Get or create demo conversation
    conversation = await conv_service.get_or_create_conversation(
        db,
        instagram_user_id=DEMO_USER_ID,
        username=DEMO_USERNAME,
    )

    # Store user message
    await conv_service.add_message(
        db,
        conversation_id=conversation.id,
        sender="user",
        content=body.message,
        instagram_message_id=f"demo_msg_{int(datetime.now(timezone.utc).timestamp())}",
    )

    # Get conversation history for context
    history = await conv_service.get_conversation_history(db, conversation.id)

    # Generate AI response
    bot_reply = await ai_agent.generate_response(
        db=db,
        user_message=body.message,
        conversation_history=history,
        username=DEMO_USERNAME,
        conversation_id=conversation.id,
        instagram_user_id=DEMO_USER_ID,
    )

    # Store bot reply
    await conv_service.add_message(
        db,
        conversation_id=conversation.id,
        sender="bot",
        content=bot_reply,
        instagram_message_id=f"demo_bot_{int(datetime.now(timezone.utc).timestamp())}",
    )

    await db.commit()

    logger.info("Demo chat: user=%s → bot=%s", body.message[:60], bot_reply[:60])

    return DemoChatResponse(
        user_message=body.message,
        bot_reply=bot_reply,
        conversation_id=conversation.id,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/reset")
async def reset_demo(db: AsyncSession = Depends(get_db)):
    """Clear the demo conversation history to start fresh."""
    from sqlalchemy import select, delete
    from app.models import Conversation, Message

    result = await db.execute(
        select(Conversation).where(Conversation.instagram_user_id == DEMO_USER_ID)
    )
    conv = result.scalar_one_or_none()

    if conv:
        await db.execute(delete(Message).where(Message.conversation_id == conv.id))
        await db.delete(conv)
        await db.commit()

    return {"status": "reset", "message": "Demo conversation cleared"}
