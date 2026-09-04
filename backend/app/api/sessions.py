import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db_models import Session as SessionModel, Message
from app.models.schemas import SessionCreate, SessionOut, MessageOut

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])

@router.post("", response_model=SessionOut)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = SessionModel(title=body.title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

@router.get("/{session_id}", response_model=list[MessageOut])
async def get_session_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(400, "Invalid session_id")
    result = await db.execute(
        select(Message).where(Message.session_id == sid).order_by(Message.created_at)
    )
    return result.scalars().all()