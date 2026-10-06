import os
import json
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("ragforge.database")

# Setup database engine
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session and ensures closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_vector_dimension_if_needed(db_engine):
    """
    Ensure the vector storage matches settings.EMBEDDING_DIMENSIONS.
    If PostgreSQL column has a different dimension, migrate the column type to vector(new_dim)
    and reset affected documents so they can be cleanly re-embedded.
    """
    dialect_name = db_engine.dialect.name
    target_dim = settings.EMBEDDING_DIMENSIONS

    if dialect_name == "postgresql":
        try:
            with db_engine.connect() as conn:
                check_sql = text("""
                    SELECT atttypmod 
                    FROM pg_attribute 
                    WHERE attrelid = 'document_chunks'::regclass 
                      AND attname = 'embedding' 
                      AND NOT attisdropped;
                """)
                res = conn.execute(check_sql).scalar()
                if res is not None and res != target_dim:
                    logger.warning(
                        f"Detected vector dimension mismatch in PostgreSQL: current={res}, target={target_dim}. "
                        f"Migrating document_chunks.embedding column to vector({target_dim})."
                    )
                    conn.execute(text(f"""
                        ALTER TABLE document_chunks 
                        ALTER COLUMN embedding TYPE vector({target_dim}) 
                        USING NULL;
                    """))
                    conn.execute(text("""
                        UPDATE documents 
                        SET processing_status = 'UPLOADED',
                            error_message = 'Embedding provider/dimension changed. Please re-process to generate new embeddings.'
                        WHERE processing_status = 'COMPLETED';
                    """))
                    conn.commit()
                    logger.info("Successfully migrated PostgreSQL vector dimension.")
        except Exception as e:
            logger.debug(f"PostgreSQL vector dimension check skipped: {e}")

    elif dialect_name == "sqlite":
        try:
            with db_engine.connect() as conn:
                tbl_check = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='document_chunks';")).scalar()
                if tbl_check:
                    rows = conn.execute(text("SELECT id, document_id, embedding FROM document_chunks WHERE embedding IS NOT NULL LIMIT 50;")).fetchall()
                    mismatched_docs = set()
                    for chunk_id, doc_id, emb_val in rows:
                        if isinstance(emb_val, str):
                            try:
                                emb_list = json.loads(emb_val)
                                if isinstance(emb_list, list) and len(emb_list) != target_dim:
                                    mismatched_docs.add(doc_id)
                            except Exception:
                                pass
                    if mismatched_docs:
                        logger.warning(
                            f"Detected outdated embedding vectors in SQLite for documents {mismatched_docs}. "
                            f"Clearing outdated embeddings to match new target dimension {target_dim}."
                        )
                        for doc_id in mismatched_docs:
                            conn.execute(text("UPDATE document_chunks SET embedding = NULL WHERE document_id = :doc_id"), {"doc_id": doc_id})
                            conn.execute(text("UPDATE documents SET processing_status = 'UPLOADED', error_message = 'Embedding provider/dimension changed. Please re-process.' WHERE id = :doc_id"), {"doc_id": doc_id})
                        conn.commit()
        except Exception as e:
            logger.debug(f"SQLite vector dimension check skipped: {e}")


def init_db():
    """Initializes tables and extensions if PostgreSQL."""
    # Ensure uploads directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # If postgresql, attempt to create pgvector extension
    if "postgresql" in settings.DATABASE_URL:
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
        except Exception as e:
            logger.debug(f"Could not create vector extension (may already exist): {e}")

    # Create all defined tables
    Base.metadata.create_all(bind=engine)

    # Perform safe dimension migration if switching between 1536 (OpenAI) and 768 (Gemini)
    migrate_vector_dimension_if_needed(engine)
