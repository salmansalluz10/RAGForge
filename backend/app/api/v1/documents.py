from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentChunkResponse,
    DocumentChunksListResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    collection_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Securely upload a document (PDF, DOCX, TXT) with validation and virus/traversal protection.
    """
    doc = await DocumentService.upload_document(
        db=db,
        user_id=current_user.id,
        file=file,
        collection_id=collection_id,
    )
    doc_dict = DocumentResponse.model_validate(doc).model_dump()
    doc_dict["chunk_count"] = len(doc.chunks) if doc.chunks else 0
    return DocumentResponse(**doc_dict)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    search: Optional[str] = Query(None, description="Search by original filename"),
    status: Optional[str] = Query(None, description="Filter by processing status"),
    collection_id: Optional[str] = Query(None, description="Filter by collection"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all uploaded documents belonging to the authenticated user.
    """
    docs, total = DocumentService.list_documents(
        db=db,
        user_id=current_user.id,
        collection_id=collection_id,
        search=search,
        status_filter=status,
        skip=skip,
        limit=limit,
    )
    items = []
    for d in docs:
        d_dict = DocumentResponse.model_validate(d).model_dump()
        d_dict["chunk_count"] = len(d.chunks) if d.chunks else 0
        items.append(DocumentResponse(**d_dict))

    return DocumentListResponse(items=items, total=total)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve document metadata for a single user-owned document.
    """
    doc = DocumentService.get_document_by_id(db, document_id, current_user.id)
    doc_dict = DocumentResponse.model_validate(doc).model_dump()
    doc_dict["chunk_count"] = len(doc.chunks) if doc.chunks else 0
    return DocumentResponse(**doc_dict)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Permanently delete a document and its stored file and chunks.
    """
    DocumentService.delete_document(db, document_id, current_user.id)
    return None


@router.post("/{document_id}/process", response_model=DocumentResponse)
def process_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger text extraction and chunking pipeline for an uploaded document.
    """
    from app.services.processing_service import ProcessingService

    doc = ProcessingService.process_document(db, document_id, current_user.id)
    doc_dict = DocumentResponse.model_validate(doc).model_dump()
    doc_dict["chunk_count"] = len(doc.chunks) if doc.chunks else 0
    return DocumentResponse(**doc_dict)


@router.get("/{document_id}/chunks", response_model=DocumentChunksListResponse)
def get_document_chunks(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all processed chunks and metadata for a document.
    """
    from app.services.processing_service import ProcessingService

    chunks = ProcessingService.get_document_chunks(db, document_id, current_user.id)
    return DocumentChunksListResponse(
        document_id=document_id,
        chunks=[DocumentChunkResponse.model_validate(c) for c in chunks],
        total=len(chunks),
    )
