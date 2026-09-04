from sentence_transformers import SentenceTransformer
from app.config import get_settings

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        settings = get_settings()
        model_name = settings.embedding_model.replace("sentence-transformers/", "")
        _model = SentenceTransformer(model_name)
    return _model

async def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text).tolist()