from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CollectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CollectionResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    document_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CollectionListResponse(BaseModel):
    items: List[CollectionResponse]
    total: int


class AddDocumentToCollection(BaseModel):
    document_id: str
