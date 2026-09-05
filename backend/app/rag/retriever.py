from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class TranscriptRetriever:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def retrieve_relevant_chunks(
        self,
        query_vector: list[float],
        top_k: int = 5,
        similarity_threshold: float = 0.35,
    ) -> list[dict]:
        stmt = text("""
            SELECT
                episode_title,
                guest_name,
                chunk_text,
                timestamp_ref,
                1 - (embedding <=> CAST(:vector AS vector)) AS similarity_score
            FROM transcript_chunks
            WHERE 1 - (embedding <=> CAST(:vector AS vector)) >= :threshold
            ORDER BY similarity_score DESC
            LIMIT :limit
        """)
        result = await self.session.execute(
            stmt,
            {"vector": str(query_vector), "threshold": similarity_threshold, "limit": top_k},
        )
        rows = result.fetchall()
        return [
            {
                "episode": r.episode_title,
                "guest": r.guest_name,
                "text": r.chunk_text,
                "timestamp": r.timestamp_ref,
                "score": float(r.similarity_score),
            }
            for r in rows
        ]