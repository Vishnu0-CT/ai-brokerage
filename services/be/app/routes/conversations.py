from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.conversation import Conversation, Message
from app.schemas.conversation import ConversationCreate, MessageCreate
from app.seed import DEFAULT_USER_ID

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("")
async def create_conversation(
    body: ConversationCreate,
    session: AsyncSession = Depends(get_session),
):
    conv = Conversation(user_id=DEFAULT_USER_ID, title=body.title)
    session.add(conv)
    await session.commit()
    await session.refresh(conv)
    return {"id": str(conv.id), "title": conv.title, "created_at": conv.created_at.isoformat()}


@router.get("")
async def list_conversations(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == DEFAULT_USER_ID)
        .order_by(Conversation.updated_at.desc())
    )
    convs = result.scalars().all()
    return [
        {"id": str(c.id), "title": c.title, "created_at": c.created_at.isoformat()}
        for c in convs
    ]


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()

    return {
        "id": str(conv.id),
        "title": conv.title,
        "messages": [
            {
                "id": str(m.id), "role": m.role,
                "content": m.content, "tool_data": m.tool_data,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }


@router.put("/{conversation_id}")
async def update_conversation(
    conversation_id: uuid.UUID,
    body: ConversationCreate,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conv.title = body.title
    await session.commit()
    await session.refresh(conv)
    return {"id": str(conv.id), "title": conv.title, "created_at": conv.created_at.isoformat()}


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await session.delete(conv)
    await session.commit()
    return {"status": "deleted"}


@router.post("/{conversation_id}/messages")
async def save_message(
    conversation_id: uuid.UUID,
    body: MessageCreate,
    session: AsyncSession = Depends(get_session),
):
    # Verify conversation exists
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg = Message(
        conversation_id=conversation_id,
        role=body.role,
        content=body.content,
        tool_data=body.tool_data,
    )
    session.add(msg)
    
    # Auto-generate title from first user message if title is generic
    if body.role == "user" and conv.title in ["Assistant", "New Chat", "Coach"]:
        # Use first 50 characters of the message as title
        new_title = body.content[:50].strip()
        if len(body.content) > 50:
            new_title += "..."
        conv.title = new_title
    
    await session.commit()
    await session.refresh(msg)

    return {
        "id": str(msg.id),
        "role": msg.role,
        "content": msg.content,
        "tool_data": msg.tool_data,
        "created_at": msg.created_at.isoformat(),
    }


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    # Verify conversation exists
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .offset(offset)
        .limit(limit)
    )
    messages = msg_result.scalars().all()

    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "tool_data": m.tool_data,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
