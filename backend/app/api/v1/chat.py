from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.chat_service import ChatService
from app.schemas.chat import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    MessageCreate,
    MessageResponse,
)

router = APIRouter(prefix="/conversations", tags=["Conversations & Chat"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = ChatService.create_conversation(
        db=db,
        user_id=current_user.id,
        title=data.title,
        collection_id=data.collection_id,
    )
    conv_dict = ConversationResponse.model_validate(conv).model_dump()
    conv_dict["message_count"] = 0
    return ConversationResponse(**conv_dict)


@router.get("", response_model=ConversationListResponse)
def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    convs, total = ChatService.list_conversations(db, current_user.id, skip=skip, limit=limit)
    items = []
    for c in convs:
        c_dict = ConversationResponse.model_validate(c).model_dump()
        c_dict["message_count"] = len(c.messages) if c.messages else 0
        items.append(ConversationResponse(**c_dict))

    return ConversationListResponse(items=items, total=total)


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = ChatService.get_conversation(db, conversation_id, current_user.id)
    c_dict = ConversationResponse.model_validate(conv).model_dump()
    c_dict["message_count"] = len(conv.messages) if conv.messages else 0
    c_dict["messages"] = [MessageResponse.model_validate(m) for m in conv.messages]
    return ConversationDetailResponse(**c_dict)


@router.put("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: str,
    data: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = ChatService.update_conversation(db, conversation_id, current_user.id, data.title)
    c_dict = ConversationResponse.model_validate(conv).model_dump()
    c_dict["message_count"] = len(conv.messages) if conv.messages else 0
    return ConversationResponse(**c_dict)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ChatService.delete_conversation(db, conversation_id, current_user.id)
    return None


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    conversation_id: str,
    data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Post a user message in the conversation and receive a grounded RAG response with citations.
    """
    msg = ChatService.send_message(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        content=data.content,
    )
    return MessageResponse.model_validate(msg)
