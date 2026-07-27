from typing import List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_service import log_event
from app.models.log import LogType
from app.models.message import DirectMessage
from app.models.user import User, RoleEnum
from app.permissions import require_role
from app.schemas import MessageCreate, MessageOut, ConversationSummary

router = APIRouter(prefix="/messenger", tags=["messenger"])


@router.post("/send", response_model=MessageOut, status_code=201)
def send_message(
    payload: MessageCreate,
    request: Request,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else None

    if payload.to_user_id == current_user.id:
        log_event(
            db, LogType.SYSTEM_MESSENGER_LOG_ERROR,
            action="send_message_failed_self",
            actor_user_id=current_user.id,
            ip_address=ip,
        )
        raise HTTPException(status_code=400, detail="Nelze poslat zprávu sám sobě")

    recipient = db.query(User).filter(User.id == payload.to_user_id).first()
    if not recipient:
        log_event(
            db, LogType.SYSTEM_MESSENGER_LOG_ERROR,
            action="send_message_failed_recipient_not_found",
            actor_user_id=current_user.id,
            target=str(payload.to_user_id),
            ip_address=ip,
        )
        raise HTTPException(status_code=404, detail="Příjemce nenalezen")

    if not payload.text.strip():
        log_event(
            db, LogType.SYSTEM_MESSENGER_LOG_ERROR,
            action="send_message_failed_empty_text",
            actor_user_id=current_user.id,
            target=str(payload.to_user_id),
            ip_address=ip,
        )
        raise HTTPException(status_code=400, detail="Zpráva nemůže být prázdná")

    message = DirectMessage(
        from_user_id=current_user.id,
        to_user_id=payload.to_user_id,
        text=payload.text,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    # Obecný messenger log
    log_event(
        db, LogType.SYSTEM_MESSENGER_LOG,
        action="message_sent",
        actor_user_id=current_user.id,
        target=str(payload.to_user_id),
        ip_address=ip,
    )
    # Specifické income/sent logy dle DEVLOG.md sekce 2
    log_event(
        db, LogType.SYSTEM_MODULE_MESSENGER_SENT_LOG_FULL,
        action="dm_sent",
        actor_user_id=current_user.id,
        target=str(payload.to_user_id),
        ip_address=ip,
        meta={"message_id": message.id, "text_len": len(payload.text)},
    )
    log_event(
        db, LogType.SYSTEM_MODULE_MESSENGER_INCOME_LOG_FULL,
        action="dm_received",
        actor_user_id=payload.to_user_id,
        target=str(current_user.id),
        ip_address=ip,
        meta={"message_id": message.id, "text_len": len(payload.text)},
    )
    return message


@router.get("/conversations", response_model=List[ConversationSummary])
def list_conversations(
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    """Seznam konverzací seskupených podle druhé strany, seřazeno dle poslední zprávy."""
    messages = (
        db.query(DirectMessage)
        .filter(
            or_(
                DirectMessage.from_user_id == current_user.id,
                DirectMessage.to_user_id == current_user.id,
            )
        )
        .order_by(DirectMessage.sent_at.desc())
        .all()
    )

    conversations = {}
    for m in messages:
        other_id = m.to_user_id if m.from_user_id == current_user.id else m.from_user_id
        if other_id not in conversations:
            unread = sum(
                1 for mm in messages
                if mm.from_user_id == other_id
                and mm.to_user_id == current_user.id
                and mm.read_at is None
            )
            conversations[other_id] = ConversationSummary(
                other_user_id=other_id,
                last_message=m.text,
                last_sent_at=m.sent_at,
                unread_count=unread,
            )

    return list(conversations.values())


@router.get("/conversation/{other_user_id}", response_model=List[MessageOut])
def read_conversation(
    other_user_id: int,
    current_user: User = Depends(require_role(RoleEnum.USER)),
    db: Session = Depends(get_db),
):
    """Historie konverzace s daným uživatelem + označení příchozích zpráv jako přečtených."""
    messages = (
        db.query(DirectMessage)
        .filter(
            or_(
                and_(
                    DirectMessage.from_user_id == current_user.id,
                    DirectMessage.to_user_id == other_user_id,
                ),
                and_(
                    DirectMessage.from_user_id == other_user_id,
                    DirectMessage.to_user_id == current_user.id,
                ),
            )
        )
        .order_by(DirectMessage.sent_at.asc())
        .all()
    )

    now = datetime.now(timezone.utc)
    for m in messages:
        if m.to_user_id == current_user.id and m.read_at is None:
            m.read_at = now
    db.commit()

    return messages
