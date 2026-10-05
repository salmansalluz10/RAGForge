import os
from typing import Optional, List, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.document import Document, DocumentChunk
from app.core.config import settings
from app.utils.file_utils import (
    sanitize_filename,
    get_file_extension,
    generate_unique_filename,
    get_storage_path,
    remove_stored_file,
)


class DocumentService:
    @staticmethod
    async def upload_document(
        db: Session,
        user_id: str,
        file: UploadFile,
        collection_id: Optional[str] = None,
    ) -> Document:
        # Validate filename and extension
        raw_filename = file.filename or "unnamed_document"
        clean_filename = sanitize_filename(raw_filename)
        file_ext = get_file_extension(clean_filename)

        # Generate unique stored filename
        unique_name = generate_unique_filename(file_ext)
        dest_path = get_storage_path(unique_name)

        # Stream write to disk while validating maximum file size
        total_size = 0
        chunk_size = 1024 * 1024  # 1 MB chunk

        try:
            with open(dest_path, "wb") as f:
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    total_size += len(chunk)
                    if total_size > settings.MAX_FILE_SIZE_BYTES:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
                        )
                    f.write(chunk)
        except Exception as e:
            # Clean up partially written file if write failed or limit exceeded
            if dest_path.exists():
                dest_path.unlink()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save uploaded file: {str(e)}",
            )

        # Create database record
        doc = Document(
            user_id=user_id,
            collection_id=collection_id,
            original_filename=clean_filename,
            stored_filename=unique_name,
            file_type=file_ext,
            file_size=total_size,
            processing_status="UPLOADED",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def list_documents(
        db: Session,
        user_id: str,
        collection_id: Optional[str] = None,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Document], int]:
        # Always filter by current user's ID
        query = db.query(Document).filter(Document.user_id == user_id)

        if collection_id:
            query = query.filter(Document.collection_id == collection_id)
        if status_filter:
            query = query.filter(Document.processing_status == status_filter.upper())
        if search:
            query = query.filter(Document.original_filename.ilike(f"%{search.strip()}%"))

        total = query.count()
        documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
        return documents, total

    @staticmethod
    def get_document_by_id(db: Session, document_id: str, user_id: str) -> Document:
        doc = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id,
        ).first()

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )
        return doc

    @staticmethod
    def delete_document(db: Session, document_id: str, user_id: str) -> None:
        doc = DocumentService.get_document_by_id(db, document_id, user_id)
        
        # Remove physical file
        remove_stored_file(doc.stored_filename)

        # Delete database record (cascade deletes chunks)
        db.delete(doc)
        db.commit()
