"""Conversation manager — handles persistence of conversations and messages."""

import logging
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Conversation, Message, ConversationStatus

logger = logging.getLogger(__name__)


async def get_or_create_conversation(
    db: AsyncSession,
    instagram_user_id: str,
    username: Optional[str] = None,
    profile_pic_url: Optional[str] = None,
) -> Conversation:
    """Find an existing conversation or create a new one.

    Args:
        db: Database session.
        instagram_user_id: The Instagram-scoped user ID.
        username: Optional username to store.
        profile_pic_url: Optional profile picture URL.

    Returns:
        The Conversation record.
    """
    result = await db.execute(
        select(Conversation).where(Conversation.instagram_user_id == instagram_user_id)
    )
    conversation = result.scalar_one_or_none()

    if conversation:
        # Update last activity and reactivate if expired
        conversation.last_message_at = datetime.now(timezone.utc)
        if conversation.status == ConversationStatus.EXPIRED.value:
            conversation.status = ConversationStatus.ACTIVE.value
        if username and not conversation.username:
            conversation.username = username
        if profile_pic_url and not conversation.profile_pic_url:
            conversation.profile_pic_url = profile_pic_url
        await db.flush()
        return conversation

    # Create new conversation
    conversation = Conversation(
        instagram_user_id=instagram_user_id,
        username=username,
        profile_pic_url=profile_pic_url,
        status=ConversationStatus.ACTIVE.value,
    )
    db.add(conversation)
    await db.flush()
    logger.info("New conversation created for user %s (id=%s)", instagram_user_id, conversation.id)
    return conversation


async def add_message(
    db: AsyncSession,
    conversation_id: int,
    sender: str,
    content: str,
    instagram_message_id: Optional[str] = None,
) -> Message:
    """Persist a message to the database.

    Args:
        db: Database session.
        conversation_id: The conversation to add the message to.
        sender: 'user', 'bot', or 'operator'.
        content: The message content text.
        instagram_message_id: Optional Instagram message ID (mid).

    Returns:
        The created Message record.
    """
    message = Message(
        conversation_id=conversation_id,
        sender=sender,
        content=content,
        instagram_message_id=instagram_message_id,
    )
    db.add(message)
    await db.flush()
    return message


async def get_conversation_history(
    db: AsyncSession,
    conversation_id: int,
    limit: int = 20,
) -> List[Message]:
    """Retrieve recent messages for a conversation (for LangChain context).

    Args:
        db: Database session.
        conversation_id: The conversation ID.
        limit: Maximum number of messages to retrieve.

    Returns:
        List of Message records ordered by timestamp (oldest first).
    """
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.desc())
        .limit(limit)
    )
    messages = list(result.scalars().all())
    messages.reverse()  # Oldest first for context
    return messages


async def get_all_conversations(db: AsyncSession) -> List[dict]:
    """Get all conversations with their latest message preview.

    Returns:
        List of conversation dicts with last_message preview.
    """
    result = await db.execute(
        select(Conversation).order_by(Conversation.last_message_at.desc())
    )
    conversations = result.scalars().all()

    previews = []
    for conv in conversations:
        # Get latest message
        msg_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.timestamp.desc())
            .limit(1)
        )
        last_msg = msg_result.scalar_one_or_none()

        previews.append({
            "id": conv.id,
            "instagram_user_id": conv.instagram_user_id,
            "username": conv.username,
            "profile_pic_url": conv.profile_pic_url,
            "last_message_at": conv.last_message_at,
            "status": conv.status,
            "last_message": last_msg.content if last_msg else None,
            "unread_count": 0,
        })

    return previews


async def get_conversation_with_messages(
    db: AsyncSession,
    conversation_id: int,
) -> Optional[dict]:
    """Get a full conversation with all messages.

    Args:
        db: Database session.
        conversation_id: The conversation ID.

    Returns:
        Dict with conversation data and messages, or None.
    """
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()

    if not conv:
        return None

    return {
        "id": conv.id,
        "instagram_user_id": conv.instagram_user_id,
        "username": conv.username,
        "profile_pic_url": conv.profile_pic_url,
        "started_at": conv.started_at,
        "last_message_at": conv.last_message_at,
        "status": conv.status,
        "is_within_window": conv.is_within_window,
        "messages": [
            {
                "id": m.id,
                "sender": m.sender,
                "content": m.content,
                "instagram_message_id": m.instagram_message_id,
                "timestamp": m.timestamp,
            }
            for m in conv.messages
        ],
    }


async def get_stats(db: AsyncSession) -> dict:
    """Get aggregate dashboard statistics."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Total conversations
    total_conv = await db.execute(select(func.count(Conversation.id)))
    total_conversations = total_conv.scalar() or 0

    # Active conversations (within 24h window)
    active_conv = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.status == ConversationStatus.ACTIVE.value
        )
    )
    active_conversations = active_conv.scalar() or 0

    # Total messages
    total_msg = await db.execute(select(func.count(Message.id)))
    total_messages = total_msg.scalar() or 0

    # Messages today
    today_msg = await db.execute(
        select(func.count(Message.id)).where(Message.timestamp >= today_start)
    )
    messages_today = today_msg.scalar() or 0

    # Bot messages
    bot_msg = await db.execute(
        select(func.count(Message.id)).where(Message.sender == "bot")
    )
    bot_messages = bot_msg.scalar() or 0

    # User messages
    user_msg = await db.execute(
        select(func.count(Message.id)).where(Message.sender == "user")
    )
    user_messages = user_msg.scalar() or 0

    return {
        "total_conversations": total_conversations,
        "active_conversations": active_conversations,
        "total_messages": total_messages,
        "messages_today": messages_today,
        "bot_messages": bot_messages,
        "user_messages": user_messages,
    }
