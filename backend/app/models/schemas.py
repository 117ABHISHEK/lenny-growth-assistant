import uuid
from datetime import datetime
from pydantic import BaseModel

class SessionCreate(BaseModel):
    title: str = "New Chat"

class SessionOut(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    class Config:
        from_attributes = True

class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    sources: dict | None = None
    created_at: datetime
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    session_id: str
    message: str
    mode: str = "default"       # "default" | "ship30"
    provider: str = "ollama"    # "ollama" | "anthropic"

class HealthStatus(BaseModel):
    status: str
    database: bool
    ollama: bool
    vector_index: bool