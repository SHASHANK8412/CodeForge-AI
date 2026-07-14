from __future__ import annotations

from pydantic import BaseModel, Field


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    first_message: str | None = Field(default=None, max_length=4000)


class ChatMessageRequest(BaseModel):
    conversation_id: str | None = Field(default=None, min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=12000)


class ConversationRenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class ConversationListQuery(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    search: str | None = Field(default=None, max_length=120)
