import json
import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.models.db_models import Message
from app.models.schemas import ChatRequest
from app.rag.retriever import TranscriptRetriever
from app.rag.embeddings import embed_text
from app.providers.ollama_provider import OllamaProvider
from app.providers.cloud_provider import AnthropicProvider
from app.skills.artifact_generator import GROUNDED_SYSTEM_PROMPT, build_context_block
from app.skills.ship30_writer import build_ship30_prompt

router = APIRouter(prefix="/api/chat", tags=["Chat"])

def get_provider(name: str):
    settings = get_settings()
    if name == "anthropic":
        return AnthropicProvider(settings.anthropic_api_key)
    return OllamaProvider(settings.ollama_base_url, settings.ollama_model)

@router.post("")
async def stream_chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    session_id = uuid.UUID(req.session_id)

    user_msg = Message(session_id=session_id, role="user", content=req.message)
    db.add(user_msg)
    await db.commit()

    retriever = TranscriptRetriever(db)
    query_vector = await embed_text(req.message)
    # Ship30 essays benefit from more context chunks than a quick Q&A
    top_k = 8 if req.mode == "ship30" else 5
    chunks = await retriever.retrieve_relevant_chunks(query_vector, top_k=top_k)
    context = build_context_block(chunks)

    if req.mode == "ship30":
        system_prompt = "You are a skilled ghostwriter. Follow the instructions in the user message exactly."
        user_content = build_ship30_prompt(req.message, context)
        llm_messages = [{"role": "user", "content": user_content}]
    else:
        system_prompt = GROUNDED_SYSTEM_PROMPT.format(context=context)
        llm_messages = [{"role": "user", "content": req.message}]

    llm = get_provider(req.provider)

    async def event_stream():
        citations = [{"episode": c["episode"], "guest": c["guest"], "score": round(c["score"], 3)} for c in chunks]
        yield f"data: {json.dumps({'type': 'sources', 'content': citations})}\n\n"

        full_response = ""
        async for token in llm.generate_response(llm_messages, system_prompt):
            full_response += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        assistant_msg = Message(
            session_id=session_id, role="assistant", content=full_response,
            sources={"citations": citations, "mode": req.mode},
        )
        db.add(assistant_msg)
        await db.commit()

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.get("/ping")
async def ping():
    return {"status": "chat router active"}