from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.providers.ollama_provider import OllamaProvider
from app.models.schemas import HealthStatus

router = APIRouter(prefix="/api", tags=["Health"])

@router.get("/health", response_model=HealthStatus)
async def health_check(db: AsyncSession = Depends(get_db)):
    settings = get_settings()

    db_ok = False
    vector_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
        result = await db.execute(text("SELECT COUNT(*) FROM transcript_chunks"))
        vector_ok = result.scalar() > 0
    except Exception:
        pass

    ollama = OllamaProvider(settings.ollama_base_url, settings.ollama_model)
    ollama_ok = await ollama.is_available()

    overall = "healthy" if (db_ok and vector_ok) else "degraded"
    return HealthStatus(status=overall, database=db_ok, ollama=ollama_ok, vector_index=vector_ok)