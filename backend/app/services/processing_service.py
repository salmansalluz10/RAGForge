import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.document import Document, DocumentChunk
from app.utils.file_utils import get_storage_path
from app.rag.extractors import ExtractorFactory
from app.rag.text_splitter import RecursiveCharacterTextSplitter
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore

logger = logging.getLogger("ragforge.processing")


class ProcessingService:
    @staticmethod
    def process_document(db: Session, document_id: str, user_id: str) -> Document:
        """
        Full document processing pipeline:
        File → Text Extraction → Normalization → Chunking → Embedding → Vector Storage → COMPLETED
        """
        # Fetch document ensuring ownership
        doc = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id,
        ).first()

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        # Update status to PROCESSING
        doc.processing_status = "PROCESSING"
        doc.error_message = None
        db.commit()
        db.refresh(doc)

        try:
            # 1. Resolve stored file
            file_path = get_storage_path(doc.stored_filename)
            if not file_path.exists():
                raise FileNotFoundError(f"Stored file '{doc.stored_filename}' not found.")

            # 2. Extract content with page preservation
            extractor = ExtractorFactory.get_extractor(doc.file_type)
            extracted_pages = extractor.extract(file_path)

            if not extracted_pages:
                raise ValueError("No readable text could be extracted from the document.")

            # 3. Chunk text recursively with metadata
            splitter = RecursiveCharacterTextSplitter()
            chunks = splitter.split_extracted_content(
                extracted_pages=extracted_pages,
                document_id=doc.id,
                document_name=doc.original_filename,
                file_type=doc.file_type,
            )

            if not chunks:
                raise ValueError("Document yielded 0 chunks after text splitting.")

            # 4. Remove any prior chunks (idempotent reprocessing support)
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
            db.flush()

            # 5. Insert new chunks WITHOUT embeddings first
            db_chunks = []
            for c in chunks:
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    chunk_metadata=c.metadata,
                    embedding=None,
                )
                db_chunks.append(db_chunk)

            db.bulk_save_objects(db_chunks)
            db.flush()

            # 6. Generate embeddings in batch
            embedding_service = EmbeddingService.get_instance()
            chunk_texts = [c.content for c in chunks]

            logger.info(
                f"Generating {len(chunk_texts)} embeddings for document {doc.id} "
                f"using {embedding_service.provider_name}"
            )

            try:
                vectors = embedding_service.embed_documents(chunk_texts)
            except Exception as emb_err:
                # Embeddings are important but we don't fail the whole pipeline
                # Document is still marked COMPLETED, chunks are stored without embeddings
                logger.warning(
                    f"Embedding generation failed for document {doc.id}: {emb_err}. "
                    f"Chunks saved without embeddings — similarity search will be unavailable."
                )
                vectors = [None] * len(chunks)

            # 7. Re-fetch inserted chunks and assign embeddings
            inserted_chunks = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.document_id == doc.id)
                .order_by(DocumentChunk.chunk_index.asc())
                .all()
            )

            for db_chunk, vec in zip(inserted_chunks, vectors):
                if vec is not None:
                    db_chunk.embedding = vec
                    db.add(db_chunk)

            # 8. Update document to COMPLETED
            page_numbers = [p.page_number for p in extracted_pages if p.page_number is not None]
            doc.page_count = max(page_numbers) if page_numbers else 1
            doc.processing_status = "COMPLETED"
            doc.error_message = None
            db.commit()
            db.refresh(doc)
            logger.info(
                f"Document {doc.id} processed: {len(chunks)} chunks, "
                f"{sum(1 for v in vectors if v)} with embeddings."
            )
            return doc

        except Exception as e:
            db.rollback()
            error_msg = str(e)
            logger.error(f"Error processing document {doc.id}: {error_msg}")
            # Safe failure: document marked FAILED, server keeps running
            doc.processing_status = "FAILED"
            doc.error_message = error_msg
            db.commit()
            db.refresh(doc)
            return doc

    @staticmethod
    def get_document_chunks(db: Session, document_id: str, user_id: str) -> list[DocumentChunk]:
        """Fetch chunks for a specific user-owned document."""
        doc = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id,
        ).first()

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        return (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .all()
        )
