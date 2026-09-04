"""Chunk and embed curated transcripts into Postgres/pgvector.
Run: python backend/scripts/ingest.py
"""
import asyncio
import sys
from pathlib import Path

import yaml
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import get_settings
from app.rag.embeddings import get_embedding_model

TRANSCRIPTS_DIR = Path(__file__).parent.parent / "data" / "transcripts"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100

def read_transcript(filepath: Path):
    content = filepath.read_text(encoding="utf-8")
    parts = content.split("---")
    if len(parts) >= 3:
        frontmatter = yaml.safe_load(parts[1])
        body = "---".join(parts[2:])
        return frontmatter, body
    return {}, content

def chunk_text(text_body: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    words = text_body.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + size])
        if chunk.strip():
            chunks.append(chunk)
        i += size - overlap
    return chunks

async def main():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    model = get_embedding_model()

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transcript_chunks (
                id SERIAL PRIMARY KEY,
                episode_title TEXT,
                guest_name TEXT,
                chunk_text TEXT,
                timestamp_ref TEXT,
                embedding vector(384)
            )
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_transcript_chunks_embedding
            ON transcript_chunks USING hnsw (embedding vector_cosine_ops)
        """))

    total_chunks = 0
    async with async_session() as session:
        for episode_dir in sorted(TRANSCRIPTS_DIR.iterdir()):
            transcript_file = episode_dir / "transcript.md"
            if not transcript_file.exists():
                continue
            frontmatter, body = read_transcript(transcript_file)
            guest = frontmatter.get("guest", episode_dir.name)
            title = frontmatter.get("title", episode_dir.name)

            chunks = chunk_text(body)
            for idx, chunk in enumerate(chunks):
                embedding = model.encode(chunk).tolist()
                await session.execute(
                    text("""
                        INSERT INTO transcript_chunks
                        (episode_title, guest_name, chunk_text, timestamp_ref, embedding)
                        VALUES (:title, :guest, :chunk, :ref, :embedding)
                    """),
                    {
                        "title": title,
                        "guest": guest,
                        "chunk": chunk,
                        "ref": f"chunk {idx + 1}",
                        "embedding": str(embedding),
                    },
                )
                total_chunks += 1
            await session.commit()
            print(f"Ingested {guest}: {len(chunks)} chunks")

    print(f"Done. Total chunks ingested: {total_chunks}")

if __name__ == "__main__":
    asyncio.run(main())