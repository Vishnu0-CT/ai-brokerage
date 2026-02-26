from __future__ import annotations

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


class TextChatRequest(BaseModel):
    message: str
