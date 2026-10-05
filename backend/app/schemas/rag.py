from typing import Optional, List
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    document_id: str
    document_name: str
    page_number: Optional[int] = None
    chunk_index: int
    score: float
    snippet: str


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)
    collection_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    top_k: Optional[int] = Field(None, ge=1, le=20)
    threshold: Optional[float] = Field(None, ge=-1.0, le=1.0)


class RAGQueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceCitation]
    chunks_retrieved: int
