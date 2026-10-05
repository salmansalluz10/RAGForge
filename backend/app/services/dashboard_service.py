from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.document import Document, DocumentChunk
from app.models.collection import Collection
from app.models.conversation import Conversation
from app.schemas.dashboard import DashboardStatsResponse
from app.schemas.document import DocumentResponse
from app.schemas.chat import ConversationResponse


class DashboardService:
    @staticmethod
    def get_stats(db: Session, user_id: str) -> DashboardStatsResponse:
        total_docs = db.query(Document).filter(Document.user_id == user_id).count()
        total_cols = db.query(Collection).filter(Collection.user_id == user_id).count()
        total_convs = db.query(Conversation).filter(Conversation.user_id == user_id).count()

        total_chunks = (
            db.query(DocumentChunk)
            .join(Document, Document.id == DocumentChunk.document_id)
            .filter(Document.user_id == user_id)
            .count()
        )

        # Status breakdown
        statuses = ["UPLOADED", "PROCESSING", "COMPLETED", "FAILED"]
        status_counts = {}
        for s in statuses:
            count = (
                db.query(Document)
                .filter(Document.user_id == user_id, Document.processing_status == s)
                .count()
            )
            status_counts[s] = count

        # Recent Documents
        recent_docs_db = (
            db.query(Document)
            .filter(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(5)
            .all()
        )
        recent_docs = []
        for d in recent_docs_db:
            d_dict = DocumentResponse.model_validate(d).model_dump()
            d_dict["chunk_count"] = len(d.chunks) if d.chunks else 0
            recent_docs.append(DocumentResponse(**d_dict))

        # Recent Conversations
        recent_convs_db = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(5)
            .all()
        )
        recent_convs = []
        for c in recent_convs_db:
            c_dict = ConversationResponse.model_validate(c).model_dump()
            c_dict["message_count"] = len(c.messages) if c.messages else 0
            recent_convs.append(ConversationResponse(**c_dict))

        return DashboardStatsResponse(
            total_documents=total_docs,
            total_collections=total_cols,
            total_conversations=total_convs,
            total_chunks=total_chunks,
            status_counts=status_counts,
            recent_documents=recent_docs,
            recent_conversations=recent_convs,
        )
