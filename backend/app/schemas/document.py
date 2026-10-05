from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    id: str
    user_id: str
    collection_id: Optional[str] = None
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    processing_status: str
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    chunk_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int


class DocumentUpdate(BaseModel):
    collection_id: Optional[str] = None


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    chunk_metadata: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunksListResponse(BaseModel):
    document_id: str
    chunks: List[DocumentChunkResponse]
    total: int
