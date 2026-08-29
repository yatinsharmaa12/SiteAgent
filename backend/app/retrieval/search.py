from app.db.database import SessionLocal
from app.ingestion.embedding import EmbeddingModel
from app.models.page_chunk import PageChunk
from app.models.page_db import Page


def search_chunks(
    query: str,
    company_id: int,
    limit: int = 5,
):
    embedder = EmbeddingModel()
    query_embedding = embedder.embed(query)

    db = SessionLocal()

    try:
        results = (
            db.query(
                PageChunk,
                Page.url,
                Page.title,
                PageChunk.embedding.cosine_distance(
                    query_embedding
                ).label("distance"),
            )
            .join(
                Page,
                Page.id == PageChunk.page_id,
            )
            .filter(
                Page.company_id == company_id
            )
            .order_by(
                PageChunk.embedding.cosine_distance(
                    query_embedding
                )
            )
            .limit(limit)
            .all()
        )

        return results

    finally:
        db.close()