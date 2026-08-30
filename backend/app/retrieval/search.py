from app.db.database import SessionLocal
from app.ingestion.embedding import EmbeddingModel
from app.models.page_chunk import PageChunk
from app.models.page_db import Page


DEFAULT_MAX_DISTANCE = 0.90


def search_chunks(
    query: str,
    company_id: int,
    limit: int = 5,
    max_distance: float = DEFAULT_MAX_DISTANCE,
):
    embedder = EmbeddingModel()
    query_embedding = embedder.embed(query)

    db = SessionLocal()

    try:
        distance = PageChunk.embedding.cosine_distance(
            query_embedding
        )

        results = (
            db.query(
                PageChunk,
                Page.url,
                Page.title,
                distance.label("distance"),
            )
            .join(
                Page,
                Page.id == PageChunk.page_id,
            )
            .filter(
                Page.company_id == company_id,
            )
            .filter(
                distance <= max_distance,
            )
            .order_by(
                distance
            )
            .limit(limit)
            .all()
        )

        return results

    finally:
        db.close()