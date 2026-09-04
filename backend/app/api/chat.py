from fastapi import APIRouter

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.get("/ping")
async def ping():
    return {"status": "chat router placeholder — full implementation in Phase 3"}