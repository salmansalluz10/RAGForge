from typing import List, Tuple, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.collection import Collection
from app.models.document import Document
from app.schemas.collection import CollectionCreate, CollectionUpdate


class CollectionService:
    @staticmethod
    def create_collection(
        db: Session,
        user_id: str,
        data: CollectionCreate,
    ) -> Collection:
        collection = Collection(
            user_id=user_id,
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
        )
        db.add(collection)
        db.commit()
        db.refresh(collection)
        return collection

    @staticmethod
    def list_collections(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Collection], int]:
        query = db.query(Collection).filter(Collection.user_id == user_id)
        total = query.count()
        collections = query.order_by(Collection.updated_at.desc()).offset(skip).limit(limit).all()
        return collections, total

    @staticmethod
    def get_collection(db: Session, collection_id: str, user_id: str) -> Collection:
        col = (
            db.query(Collection)
            .filter(Collection.id == collection_id, Collection.user_id == user_id)
            .first()
        )
        if not col:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found.",
            )
        return col

    @staticmethod
    def update_collection(
        db: Session,
        collection_id: str,
        user_id: str,
        data: CollectionUpdate,
    ) -> Collection:
        col = CollectionService.get_collection(db, collection_id, user_id)
        if data.name is not None:
            col.name = data.name.strip()
        if data.description is not None:
            col.description = data.description.strip() if data.description else None
        col.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(col)
        return col

    @staticmethod
    def delete_collection(db: Session, collection_id: str, user_id: str) -> None:
        col = CollectionService.get_collection(db, collection_id, user_id)
        # Unlink documents from this collection
        db.query(Document).filter(Document.collection_id == collection_id).update(
            {"collection_id": None},
            synchronize_session=False,
        )
        db.delete(col)
        db.commit()

    @staticmethod
    def add_document(db: Session, collection_id: str, document_id: str, user_id: str) -> Document:
        CollectionService.get_collection(db, collection_id, user_id)
        doc = (
            db.query(Document)
            .filter(Document.id == document_id, Document.user_id == user_id)
            .first()
        )
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )
        doc.collection_id = collection_id
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def remove_document(db: Session, collection_id: str, document_id: str, user_id: str) -> Document:
        CollectionService.get_collection(db, collection_id, user_id)
        doc = (
            db.query(Document)
            .filter(Document.id == document_id, Document.user_id == user_id)
            .first()
        )
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )
        if doc.collection_id == collection_id:
            doc.collection_id = None
            db.commit()
            db.refresh(doc)
        return doc
