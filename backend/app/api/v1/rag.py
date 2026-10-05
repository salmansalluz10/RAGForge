from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["RAG Pipeline"])


@router.post("/query", response_model=RAGQueryResponse)
def query_rag(
    request: RAGQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute Retrieval-Augmented Generation (RAG):
    Searches user's documents for relevant chunks, constructs context,
    invokes LLM, and returns grounded answer with source citations.
    """
    return RAGService.answer_question(
        db=db,
        question=request.question,
        user_id=current_user.id,
        collection_id=request.collection_id,
        document_ids=request.document_ids,
        top_k=request.top_k,
        threshold=request.threshold,
    )
