import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, Text, DateTime, ForeignKey, JSON
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base
from app.core.config import settings


class EmbeddingType(TypeDecorator):
    """
    Cross-dialect vector embedding type:
    Uses native pgvector Vector on PostgreSQL, and JSON Text on SQLite.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(settings.EMBEDDING_DIMENSIONS))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, (list, tuple)):
            return json.dumps(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    collection_id = Column(String(36), ForeignKey("collections.id", ondelete="SET NULL"), nullable=True, index=True)
    
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    file_type = Column(String(10), nullable=False)  # pdf, docx, txt
    file_size = Column(BigInteger, nullable=False)
    processing_status = Column(String(20), default="UPLOADED", nullable=False)  # UPLOADED, PROCESSING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="documents")
    collection = relationship("Collection", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan", order_by="DocumentChunk.chunk_index")

    def __repr__(self):
        return f"<Document {self.original_filename} ({self.processing_status})>"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_metadata = Column(JSON, nullable=True)
    embedding = Column(EmbeddingType, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<DocumentChunk doc={self.document_id} idx={self.chunk_index}>"
