"""Conversations router — dashboard API for viewing and managing conversations."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import ConversationPreview, ConversationDetail, ManualReplyRequest, DashboardStats
from app.services import conversation as conv_service
from app.services import instagram as ig_service
from app.services import ai_agent
from app.models import Conversation

from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationPreview])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    """List all conversations with latest message preview."""
    previews = await conv_service.get_all_conversations(db)
    return previews


@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get aggregate dashboard statistics."""
    stats = await conv_service.get_stats(db)
    return stats


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: int, db: AsyncSession = Depends(get_db)):
    """Get full conversation with all messages."""
    data = await conv_service.get_conversation_with_messages(db, conversation_id)
    if not data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return data


@router.post("/{conversation_id}/reply")
async def manual_reply(
    conversation_id: int,
    body: ManualReplyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a manual reply from the dashboard (operator override)."""
    # Get conversation
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not conversation.is_within_window:
        raise HTTPException(
            status_code=400,
            detail="24-hour messaging window has expired for this conversation"
        )

    # Send via Instagram
    send_result = await ig_service.send_message(
        recipient_id=conversation.instagram_user_id,
        text=body.content,
    )

    if "error" in send_result:
        raise HTTPException(status_code=502, detail=f"Instagram API error: {send_result['error']}")

    # Store operator message
    bot_mid = send_result.get("message_id")
    await conv_service.add_message(
        db,
        conversation_id=conversation.id,
        sender="operator",
        content=body.content,
        instagram_message_id=bot_mid,
    )

    await db.commit()

    return {"status": "sent", "message_id": bot_mid}
