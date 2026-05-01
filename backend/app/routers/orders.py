"""Orders router — view and manage purchase orders created by the AI."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Order
from app.schemas import OrderOut, OrderStatusUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("", response_model=List[OrderOut])
async def list_orders(db: AsyncSession = Depends(get_db)):
    """List all orders, newest first, with product details."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.product))
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.product))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}/status", response_model=OrderOut)
async def update_order_status(
    order_id: int,
    body: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an order's status (confirmed → completed / cancelled)."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.product))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = body.status
    await db.commit()
    await db.refresh(order)
    logger.info("Order #%d status → %s", order.id, body.status)
    return order
