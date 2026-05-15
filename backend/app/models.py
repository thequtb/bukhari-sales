"""Database models for the Bukhari Sales app."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, ForeignKey
)
from sqlalchemy import DateTime as _DateTime
from sqlalchemy.dialects.postgresql import TIMESTAMP as PGTS
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class MessageSender(str, enum.Enum):
    USER = "user"
    BOT = "bot"
    OPERATOR = "operator"


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CLOSED = "closed"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ── Instagram ─────────────────────────────────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    instagram_user_id = Column(String(128), unique=True, nullable=False, index=True)
    username = Column(String(128), nullable=True)
    profile_pic_url = Column(Text, nullable=True)
    # Use TIMESTAMP WITH TIME ZONE for all timestamps
    started_at = Column(PGTS(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_message_at = Column(PGTS(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default=ConversationStatus.ACTIVE.value)

    messages = relationship("Message", back_populates="conversation", order_by="Message.timestamp")
    orders = relationship("Order", back_populates="conversation")

    @property
    def is_within_window(self) -> bool:
        """Check if the 24-hour messaging window is still open."""
        if not self.last_message_at:
            return False
        now = datetime.now(timezone.utc)
        last = self.last_message_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        return (now - last).total_seconds() < 86400


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender = Column(String(20), nullable=False)  # user, bot, operator
    content = Column(Text, nullable=False)
    instagram_message_id = Column(String(256), nullable=True)
    timestamp = Column(PGTS(timezone=True), default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")


# ── Telegram ──────────────────────────────────────────────────────────────────

class TelegramConversation(Base):
    """Tracks an ongoing Telegram chat with a user."""
    __tablename__ = "telegram_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id = Column(String(128), unique=True, nullable=False, index=True)
    chat_id = Column(String(128), nullable=False)        # same as user_id for private chats
    username = Column(String(128), nullable=True)        # @handle (may be absent)
    full_name = Column(String(256), nullable=True)       # first + last name
    started_at = Column(PGTS(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_message_at = Column(PGTS(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default=ConversationStatus.ACTIVE.value)

    messages = relationship(
        "TelegramMessage", back_populates="conversation",
        order_by="TelegramMessage.timestamp"
    )
    orders = relationship("Order", back_populates="telegram_conversation")


class TelegramMessage(Base):
    """A single message in a Telegram conversation."""
    __tablename__ = "telegram_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("telegram_conversations.id"), nullable=False)
    sender = Column(String(20), nullable=False)          # user | bot
    content = Column(Text, nullable=False)
    telegram_message_id = Column(String(64), nullable=True)
    timestamp = Column(PGTS(timezone=True), default=lambda: datetime.now(timezone.utc))

    conversation = relationship("TelegramConversation", back_populates="messages")


# ── Products ──────────────────────────────────────────────────────────────────

class Product(Base):
    """A product variant within a category.

    Products with the same ``category`` are treated as variants of the same item.
    ``description`` is the shared category-level description (same for all variants).
    ``variant_name`` is the specific tier name, e.g. «Полный курс».
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)          # category display name
    variant_name = Column(String(256), nullable=True)   # e.g. "Полный курс (алфавит + таджвид)"
    description = Column(Text, nullable=True)           # shared for all variants in the category
    price = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), default="KZT")
    image_url = Column(Text, nullable=True)
    category = Column(String(128), nullable=True)       # grouping key
    in_stock = Column(Boolean, default=True)
    created_at = Column(PGTS(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(PGTS(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    orders = relationship("Order", back_populates="product")


# ── Orders ────────────────────────────────────────────────────────────────────

class Order(Base):
    """A confirmed purchase order created by the AI during conversation."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    telegram_conversation_id = Column(Integer, ForeignKey("telegram_conversations.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    instagram_user_id = Column(String(128), nullable=True)
    telegram_user_id = Column(String(128), nullable=True)
    username = Column(String(128), nullable=True)
    customer_name = Column(String(256), nullable=True)
    customer_contact = Column(String(256), nullable=True)  # phone / email / handle
    notes = Column(Text, nullable=True)
    channel = Column(String(20), default="instagram")      # instagram | telegram
    status = Column(String(50), default=OrderStatus.CONFIRMED.value)
    created_at = Column(PGTS(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(PGTS(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="orders")
    telegram_conversation = relationship("TelegramConversation", back_populates="orders")
    product = relationship("Product", back_populates="orders")


# ── AI Config ─────────────────────────────────────────────────────────────────

class AIConfig(Base):
    __tablename__ = "ai_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    system_prompt = Column(Text, nullable=False, default="You are a friendly and helpful sales assistant.")
    temperature = Column(Float, default=0.7)
    model_name = Column(String(64), default="gpt-4o-mini")
    max_tokens = Column(Integer, default=500)
