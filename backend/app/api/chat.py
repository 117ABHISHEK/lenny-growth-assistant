import json
import logging
import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.models.db_models import Message, Artifact
from app.models.schemas import ChatRequest
from app.rag.retriever import TranscriptRetriever
from app.rag.embeddings import embed_text
from app.providers.ollama_provider import OllamaProvider
from app.providers.cloud_provider import AnthropicProvider
from app.skills.artifact_generator import (
    GROUNDED_SYSTEM_PROMPT,
    ARTIFACT_INSTRUCTION,
    build_context_block,
    extract_artifacts,
    strip_artifact_tags,
    flag_unverified_citations,
)
from app.skills.ship30_writer import build_ship30_prompt

logger = logging.getLogger("lenny_assistant")

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
    top_k = 8 if req.mode == "ship30" else 5
    chunks = await retriever.retrieve_relevant_chunks(query_vector, top_k=top_k)
    context = build_context_block(chunks)

    if req.mode == "ship30":
        system_prompt = "You are a skilled ghostwriter. Follow the instructions in the user message exactly."
        user_content = build_ship30_prompt(req.message, context)
        llm_messages = [{"role": "user", "content": user_content}]
    else:
        system_prompt = GROUNDED_SYSTEM_PROMPT.format(
            context=context, artifact_instruction=ARTIFACT_INSTRUCTION
        )
        llm_messages = [{"role": "user", "content": req.message}]

    llm = get_provider(req.provider)

    async def event_stream():
        citations = [{"episode": c["episode"], "guest": c["guest"], "score": round(c["score"], 3)} for c in chunks]
        yield f"data: {json.dumps({'type': 'sources', 'content': citations})}\n\n"

        full_response = ""
        async for token in llm.generate_response(llm_messages, system_prompt):
            full_response += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        artifacts = extract_artifacts(full_response)
        clean_text = strip_artifact_tags(full_response)

        unverified = flag_unverified_citations(full_response)
        if unverified:
            logger.warning(f"Unverified citations detected (not in known corpus): {unverified}")

        assistant_msg = Message(
            session_id=session_id, role="assistant", content=clean_text,
            sources={"citations": citations, "mode": req.mode},
        )
        db.add(assistant_msg)
        await db.flush()

        for art in artifacts:
            db.add(Artifact(
                message_id=assistant_msg.id,
                artifact_type=art["artifact_type"],
                title=art["title"],
                content=art["content"],
            ))
        await db.commit()

        if artifacts:
            yield f"data: {json.dumps({'type': 'artifact', 'content': artifacts})}\n\n"

        if unverified:
            yield f"data: {json.dumps({'type': 'warning', 'content': f'Unverified citations detected: {unverified}'})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.get("/ping")
async def ping():
    return {"status": "chat router active"}