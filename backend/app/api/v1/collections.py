from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.collection_service import CollectionService
from app.schemas.collection import (
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
    CollectionListResponse,
    AddDocumentToCollection,
)
from app.schemas.document import DocumentResponse

router = APIRouter(prefix="/collections", tags=["Collections"])


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(
    data: CollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    col = CollectionService.create_collection(db, current_user.id, data)
    col_dict = CollectionResponse.model_validate(col).model_dump()
    col_dict["document_count"] = 0
    return CollectionResponse(**col_dict)


@router.get("", response_model=CollectionListResponse)
def list_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cols, total = CollectionService.list_collections(db, current_user.id, skip=skip, limit=limit)
    items = []
    for c in cols:
        c_dict = CollectionResponse.model_validate(c).model_dump()
        c_dict["document_count"] = len(c.documents) if c.documents else 0
        items.append(CollectionResponse(**c_dict))

    return CollectionListResponse(items=items, total=total)


@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(
    collection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    col = CollectionService.get_collection(db, collection_id, current_user.id)
    c_dict = CollectionResponse.model_validate(col).model_dump()
    c_dict["document_count"] = len(col.documents) if col.documents else 0
    return CollectionResponse(**c_dict)


@router.put("/{collection_id}", response_model=CollectionResponse)
def update_collection(
    collection_id: str,
    data: CollectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    col = CollectionService.update_collection(db, collection_id, current_user.id, data)
    c_dict = CollectionResponse.model_validate(col).model_dump()
    c_dict["document_count"] = len(col.documents) if col.documents else 0
    return CollectionResponse(**c_dict)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(
    collection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    CollectionService.delete_collection(db, collection_id, current_user.id)
    return None


@router.post("/{collection_id}/documents", response_model=DocumentResponse)
def add_document_to_collection(
    collection_id: str,
    data: AddDocumentToCollection,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = CollectionService.add_document(db, collection_id, data.document_id, current_user.id)
    doc_dict = DocumentResponse.model_validate(doc).model_dump()
    doc_dict["chunk_count"] = len(doc.chunks) if doc.chunks else 0
    return DocumentResponse(**doc_dict)


@router.delete("/{collection_id}/documents/{document_id}", response_model=DocumentResponse)
def remove_document_from_collection(
    collection_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = CollectionService.remove_document(db, collection_id, document_id, current_user.id)
    doc_dict = DocumentResponse.model_validate(doc).model_dump()
    doc_dict["chunk_count"] = len(doc.chunks) if doc.chunks else 0
    return DocumentResponse(**doc_dict)
