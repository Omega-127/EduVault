import json
from datetime import datetime
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.dependencies import get_db, require_admin
from app.db.models.user import User
from app.db.models.system_log import SystemLog
from app.db.models.document import Document

router = APIRouter(prefix="/admin", tags=["Admin"])


class AdminUserResponse(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminLogResponse(BaseModel):
    id: str
    event_type: str
    payload: Dict[str, Any]
    created_at: datetime


class AdminStatsResponse(BaseModel):
    total_users: int
    total_documents: int
    indexed_documents: int
    total_logs: int


@router.get("/users", response_model=List[AdminUserResponse])
async def list_users(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.get("/logs", response_model=List[AdminLogResponse])
async def list_logs(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SystemLog).order_by(SystemLog.created_at.desc()).limit(100))
    logs = result.scalars().all()

    resp = []
    for l in logs:
        try:
            pl = json.loads(l.payload) if l.payload else {}
        except Exception:
            pl = {"raw": l.payload}
        resp.append(
            AdminLogResponse(
                id=l.id,
                event_type=l.event_type,
                payload=pl,
                created_at=l.created_at,
            )
        )
    return resp


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    users_res = await db.execute(select(User))
    users_count = len(users_res.scalars().all())

    docs_res = await db.execute(select(Document))
    all_docs = docs_res.scalars().all()
    total_docs = len(all_docs)
    indexed_docs = len([d for d in all_docs if d.status == "indexed"])

    logs_res = await db.execute(select(SystemLog))
    logs_count = len(logs_res.scalars().all())

    return AdminStatsResponse(
        total_users=users_count,
        total_documents=total_docs,
        indexed_documents=indexed_docs,
        total_logs=logs_count,
    )
