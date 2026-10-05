from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.rag import SourceCitation


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: Optional[List[SourceCitation]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    title: Optional[str] = Field("New Conversation", max_length=200)
    collection_id: Optional[str] = None


class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    collection_id: Optional[str] = None
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []


class ConversationListResponse(BaseModel):
    items: List[ConversationResponse]
    total: int
