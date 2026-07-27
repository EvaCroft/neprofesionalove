from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.log import LogEntry, LogType
from app.models.user import User, RoleEnum
from app.permissions import require_role
from app.schemas import LogOut

router = APIRouter(prefix="/admin", tags=["admin-logs"])


@router.get("/logs", response_model=List[LogOut])
def read_logs(
    log_type: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
    db: Session = Depends(get_db),
):
    limit = min(limit, 500)
    query = db.query(LogEntry)
    if log_type:
        try:
            query = query.filter(LogEntry.log_type == LogType(log_type))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Neznámý log_type: {log_type}")
    return query.order_by(LogEntry.timestamp.desc()).limit(limit).all()
