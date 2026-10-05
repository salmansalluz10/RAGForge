from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/search", tags=["Semantic Search"])


class SearchRequest(BaseModel):
    query: str
    collection_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    top_k: Optional[int] = None
    threshold: Optional[float] = None


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    chunk_index: int
    page_number: Optional[int] = None
    content: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    total: int


@router.post("", response_model=SearchResponse)
def semantic_search(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Semantic similarity search across processed documents.

    Embeds the query, performs vector search in pgvector/SQLite,
    and returns ranked results from the authenticated user's documents only.
    """
    context = RetrievalService.retrieve(
        db=db,
        question=request.query,
        user_id=current_user.id,
        collection_id=request.collection_id,
        document_ids=request.document_ids,
        top_k=request.top_k,
        threshold=request.threshold,
    )

    results = [
        SearchResultItem(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            document_name=c.document_name,
            chunk_index=c.chunk_index,
            page_number=c.page_number,
            content=c.content,
            score=c.score,
        )
        for c in context.chunks
    ]

    return SearchResponse(
        query=request.query,
        results=results,
        total=len(results),
    )
