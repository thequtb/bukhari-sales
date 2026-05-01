"""Database models for the Bukhari Sales app."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
)
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


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    instagram_user_id = Column(String(128), unique=True, nullable=False, index=True)
    username = Column(String(128), nullable=True)
    profile_pic_url = Column(Text, nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_message_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default=ConversationStatus.ACTIVE.value)

    messages = relationship("Message", back_populates="conversation", order_by="Message.timestamp")
    orders = relationship("Order", back_populates="conversation")

    @property
    def is_within_window(self) -> bool:
        """Check if the 24-hour messaging window is still open."""
        if not self.last_message_at:
            return False
        now = datetime.now(timezone.utc)
        last = self.last_message_at.replace(tzinfo=timezone.utc) if self.last_message_at.tzinfo is None else self.last_message_at
        return (now - last).total_seconds() < 86400


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender = Column(String(20), nullable=False)  # user, bot, operator
    content = Column(Text, nullable=False)
    instagram_message_id = Column(String(256), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")


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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    orders = relationship("Order", back_populates="product")


class Order(Base):
    """A confirmed purchase order created by the AI during conversation."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    instagram_user_id = Column(String(128), nullable=True)
    username = Column(String(128), nullable=True)
    customer_name = Column(String(256), nullable=True)
    customer_contact = Column(String(256), nullable=True)  # phone / email / IG handle
    notes = Column(Text, nullable=True)
    status = Column(String(50), default=OrderStatus.CONFIRMED.value)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="orders")
    product = relationship("Product", back_populates="orders")


class AIConfig(Base):
    __tablename__ = "ai_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    system_prompt = Column(Text, nullable=False, default="You are a friendly and helpful sales assistant.")
    temperature = Column(Float, default=0.7)
    model_name = Column(String(64), default="gpt-4o-mini")
    max_tokens = Column(Integer, default=500)
