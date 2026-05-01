"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ── Messages ──────────────────────────────────────────────────────────────────

class MessageOut(BaseModel):
    id: int
    sender: str
    content: str
    instagram_message_id: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


# ── Conversations ─────────────────────────────────────────────────────────────

class ConversationPreview(BaseModel):
    id: int
    instagram_user_id: str
    username: Optional[str] = None
    profile_pic_url: Optional[str] = None
    last_message_at: Optional[datetime] = None
    status: str
    last_message: Optional[str] = None
    unread_count: int = 0

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    id: int
    instagram_user_id: str
    username: Optional[str] = None
    profile_pic_url: Optional[str] = None
    started_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    status: str
    is_within_window: bool
    messages: List[MessageOut] = []

    model_config = {"from_attributes": True}


class ManualReplyRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)


# ── Products ──────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    variant_name: Optional[str] = None
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    currency: str = Field(default="KZT", max_length=10)
    image_url: Optional[str] = None
    category: Optional[str] = None
    in_stock: bool = True


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=256)
    variant_name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    in_stock: Optional[bool] = None


class ProductOut(BaseModel):
    id: int
    name: str
    variant_name: Optional[str] = None
    description: Optional[str] = None
    price: float
    currency: str
    image_url: Optional[str] = None
    category: Optional[str] = None
    in_stock: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Orders ───────────────────────────────────────────────────────────────────────────

class OrderOut(BaseModel):
    id: int
    conversation_id: Optional[int] = None
    product_id: int
    instagram_user_id: Optional[str] = None
    username: Optional[str] = None
    customer_name: Optional[str] = None
    customer_contact: Optional[str] = None
    notes: Optional[str] = None
    status: str
    created_at: datetime
    product: Optional[ProductOut] = None

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|confirmed|completed|cancelled)$")


# ── AI Config ─────────────────────────────────────────────────────────────────

class AIConfigUpdate(BaseModel):
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    model_name: Optional[str] = None
    max_tokens: Optional[int] = Field(None, ge=50, le=4096)


class AIConfigOut(BaseModel):
    id: int
    system_prompt: str
    temperature: float
    model_name: str
    max_tokens: int

    model_config = {"from_attributes": True}


# ── Stats ─────────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_conversations: int = 0
    active_conversations: int = 0
    total_messages: int = 0
    messages_today: int = 0
    bot_messages: int = 0
    user_messages: int = 0
