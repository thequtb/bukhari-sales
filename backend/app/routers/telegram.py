"""Telegram admin router — exposes Telegram conversations to the admin dashboard."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import TelegramConversation, TelegramMessage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/telegram", tags=["telegram"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class TelegramMessageOut(BaseModel):
    id: int
    sender: str
    content: str
    telegram_message_id: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class TelegramConversationPreview(BaseModel):
    id: int
    telegram_user_id: str
    chat_id: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    last_message_at: Optional[datetime] = None
    status: str
    last_message: Optional[str] = None

    model_config = {"from_attributes": True}


class TelegramConversationDetail(BaseModel):
    id: int
    telegram_user_id: str
    chat_id: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    started_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    status: str
    messages: List[TelegramMessageOut] = []

    model_config = {"from_attributes": True}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/conversations", response_model=List[TelegramConversationPreview])
async def list_telegram_conversations(db: AsyncSession = Depends(get_db)):
    """List all Telegram conversations ordered by most recent activity."""
    result = await db.execute(
        select(TelegramConversation)
        .order_by(TelegramConversation.last_message_at.desc())
    )
    convs = result.scalars().all()

    previews = []
    for conv in convs:
        msg_result = await db.execute(
            select(TelegramMessage)
            .where(TelegramMessage.conversation_id == conv.id)
            .order_by(TelegramMessage.timestamp.desc())
            .limit(1)
        )
        last_msg = msg_result.scalar_one_or_none()
        previews.append(TelegramConversationPreview(
            id=conv.id,
            telegram_user_id=conv.telegram_user_id,
            chat_id=conv.chat_id,
            username=conv.username,
            full_name=conv.full_name,
            last_message_at=conv.last_message_at,
            status=conv.status,
            last_message=last_msg.content if last_msg else None,
        ))

    return previews


@router.get("/conversations/{conversation_id}", response_model=TelegramConversationDetail)
async def get_telegram_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single Telegram conversation with full message history."""
    result = await db.execute(
        select(TelegramConversation)
        .options(selectinload(TelegramConversation.messages))
        .where(TelegramConversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return TelegramConversationDetail(
        id=conv.id,
        telegram_user_id=conv.telegram_user_id,
        chat_id=conv.chat_id,
        username=conv.username,
        full_name=conv.full_name,
        started_at=conv.started_at,
        last_message_at=conv.last_message_at,
        status=conv.status,
        messages=[
            TelegramMessageOut(
                id=m.id,
                sender=m.sender,
                content=m.content,
                telegram_message_id=m.telegram_message_id,
                timestamp=m.timestamp,
            )
            for m in conv.messages
        ],
    )
