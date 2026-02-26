from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.notification import Notification
from app.seed import DEFAULT_USER_ID

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationCreate(BaseModel):
    title: str
    message: str
    context_type: str
    context_data: dict | None = None
    actions: list[dict] | None = None


class NotificationUpdate(BaseModel):
    is_read: bool | None = None
    is_dismissed: bool | None = None
    action_taken: str | None = None


@router.get("")
async def list_notifications(
    unread_only: bool = False,
    session: AsyncSession = Depends(get_session),
):
    """Get all notifications for the user"""
    query = select(Notification).where(Notification.user_id == DEFAULT_USER_ID)
    
    if unread_only:
        query = query.where(Notification.is_read == False)
    
    query = query.order_by(Notification.created_at.desc())
    
    result = await session.execute(query)
    notifications = result.scalars().all()
    
    return [
        {
            "id": str(n.id),
            "title": n.title,
            "message": n.message,
            "context_type": n.context_type,
            "context_data": n.context_data,
            "actions": n.actions,
            "is_read": n.is_read,
            "is_dismissed": n.is_dismissed,
            "action_taken": n.action_taken,
            "created_at": n.created_at.isoformat(),
            "read_at": n.read_at.isoformat() if n.read_at else None,
        }
        for n in notifications
    ]


@router.get("/unread-count")
async def get_unread_count(session: AsyncSession = Depends(get_session)):
    """Get count of unread notifications"""
    result = await session.execute(
        select(Notification)
        .where(Notification.user_id == DEFAULT_USER_ID)
        .where(Notification.is_read == False)
        .where(Notification.is_dismissed == False)
    )
    notifications = result.scalars().all()
    return {"count": len(notifications)}


@router.post("")
async def create_notification(
    body: NotificationCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new notification"""
    notification = Notification(
        user_id=DEFAULT_USER_ID,
        title=body.title,
        message=body.message,
        context_type=body.context_type,
        context_data=body.context_data,
        actions=body.actions,
    )
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    
    return {
        "id": str(notification.id),
        "title": notification.title,
        "message": notification.message,
        "context_type": notification.context_type,
        "created_at": notification.created_at.isoformat(),
    }


@router.patch("/{notification_id}")
async def update_notification(
    notification_id: uuid.UUID,
    body: NotificationUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update notification status"""
    result = await session.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    if body.is_read is not None:
        notification.is_read = body.is_read
        if body.is_read and not notification.read_at:
            notification.read_at = datetime.now(timezone.utc)
    
    if body.is_dismissed is not None:
        notification.is_dismissed = body.is_dismissed
        if body.is_dismissed and not notification.dismissed_at:
            notification.dismissed_at = datetime.now(timezone.utc)
    
    if body.action_taken is not None:
        notification.action_taken = body.action_taken
    
    await session.commit()
    await session.refresh(notification)
    
    return {
        "id": str(notification.id),
        "is_read": notification.is_read,
        "is_dismissed": notification.is_dismissed,
        "action_taken": notification.action_taken,
    }


@router.post("/mark-all-read")
async def mark_all_read(session: AsyncSession = Depends(get_session)):
    """Mark all notifications as read"""
    result = await session.execute(
        select(Notification)
        .where(Notification.user_id == DEFAULT_USER_ID)
        .where(Notification.is_read == False)
    )
    notifications = result.scalars().all()
    
    now = datetime.now(timezone.utc)
    for notification in notifications:
        notification.is_read = True
        notification.read_at = now
    
    await session.commit()
    
    return {"marked_read": len(notifications)}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete a notification"""
    result = await session.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    await session.delete(notification)
    await session.commit()
    
    return {"status": "deleted"}
