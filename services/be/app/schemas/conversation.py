from __future__ import annotations

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


class MessageCreate(BaseModel):
    role: str
    content: str
    tool_data: dict | None = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    tool_data: dict | None
    created_at: str


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    messages: list[MessageResponse] = []
