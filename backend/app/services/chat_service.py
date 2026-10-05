import logging
from typing import List, Tuple, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.conversation import Conversation, Message
from app.services.rag_service import RAGService
from app.schemas.rag import SourceCitation

logger = logging.getLogger("ragforge.chat")


class ChatService:
    @staticmethod
    def create_conversation(
        db: Session,
        user_id: str,
        title: Optional[str] = "New Conversation",
        collection_id: Optional[str] = None,
    ) -> Conversation:
        conv = Conversation(
            user_id=user_id,
            title=title or "New Conversation",
            collection_id=collection_id,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def list_conversations(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Conversation], int]:
        query = db.query(Conversation).filter(Conversation.user_id == user_id)
        total = query.count()
        conversations = query.order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
        return conversations, total

    @staticmethod
    def get_conversation(db: Session, conversation_id: str, user_id: str) -> Conversation:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
        return conv

    @staticmethod
    def update_conversation(db: Session, conversation_id: str, user_id: str, title: str) -> Conversation:
        conv = ChatService.get_conversation(db, conversation_id, user_id)
        conv.title = title.strip()
        conv.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def delete_conversation(db: Session, conversation_id: str, user_id: str) -> None:
        conv = ChatService.get_conversation(db, conversation_id, user_id)
        db.delete(conv)
        db.commit()

    @staticmethod
    def send_message(
        db: Session,
        conversation_id: str,
        user_id: str,
        content: str,
    ) -> Message:
        conv = ChatService.get_conversation(db, conversation_id, user_id)

        # 1. Save User Message
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=content.strip(),
        )
        db.add(user_msg)
        db.commit()

        # Auto-title conversation on first message
        if conv.title == "New Conversation":
            first_title = content.strip()[:40]
            if len(content.strip()) > 40:
                first_title += "..."
            conv.title = first_title

        # 2. Execute RAG pipeline scoped to the user and optional collection
        rag_res = RAGService.answer_question(
            db=db,
            question=content.strip(),
            user_id=user_id,
            collection_id=conv.collection_id,
        )

        # 3. Save Assistant Message with serialized citations
        sources_data = [s.model_dump() for s in rag_res.sources] if rag_res.sources else None
        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=rag_res.answer,
            sources=sources_data,
        )
        db.add(assistant_msg)
        conv.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(assistant_msg)

        return assistant_msg
