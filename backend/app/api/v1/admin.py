<<<<<<< HEAD
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
=======
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    ChatSession,
    Document,
    DocumentChunk,
    Feedback,
    Message,
    SystemLog,
    User,
)
from app.db.session import get_db
from app.dependencies import require_admin
from app.schemas.admin import (
    AdminStatsResponse,
    AdminUserListResponse,
    SystemLogListResponse,
    SystemLogResponse,
)
from app.schemas.auth import UserResponse
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070

router = APIRouter(prefix="/admin", tags=["Admin"])


<<<<<<< HEAD
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
=======
@router.get(
    "/logs",
    response_model=SystemLogListResponse,
    summary="Query system logs (Admin only)",
)
async def get_system_logs(
    event_type: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves system logs such as unanswerable_query and ingestion_failed events."""
    query = select(SystemLog)
    count_query = select(func.count(SystemLog.id))

    if event_type:
        query = query.where(SystemLog.event_type == event_type)
        count_query = count_query.where(SystemLog.event_type == event_type)

    total_res = await db.execute(count_query)
    total = total_res.scalar_one()

    query = query.order_by(SystemLog.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(query)
    logs = list(res.scalars().all())

    return SystemLogListResponse(
        total=total,
        logs=[SystemLogResponse.model_validate(l) for l in logs],
    )


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="List all registered users (Admin only)",
)
async def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lists registered users and their account statuses."""
    total_res = await db.execute(select(func.count(User.id)))
    total = total_res.scalar_one()

    res = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    )
    users = list(res.scalars().all())

    return AdminUserListResponse(
        total=total,
        users=[UserResponse.model_validate(u) for u in users],
    )


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="Aggregate platform usage statistics (Admin only)",
)
async def get_admin_stats(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Computes high-level aggregated counts for dashboard analytics."""
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    total_docs = (await db.execute(select(func.count(Document.id)))).scalar_one()
    total_chunks = (await db.execute(select(func.count(DocumentChunk.id)))).scalar_one()
    total_sessions = (await db.execute(select(func.count(ChatSession.id)))).scalar_one()
    total_messages = (await db.execute(select(func.count(Message.id)))).scalar_one()
    total_feedbacks = (await db.execute(select(func.count(Feedback.id)))).scalar_one()

    unans_res = await db.execute(
        select(func.count(SystemLog.id)).where(SystemLog.event_type == "unanswerable_query")
    )
    unanswerable_count = unans_res.scalar_one()

    return AdminStatsResponse(
        total_users=total_users,
        total_documents=total_docs,
        total_indexed_chunks=total_chunks,
        total_chat_sessions=total_sessions,
        total_messages=total_messages,
        total_feedbacks=total_feedbacks,
        unanswerable_queries_count=unanswerable_count,
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
    )
