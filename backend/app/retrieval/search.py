from app.db.database import SessionLocal
from app.ingestion.embedding import EmbeddingModel
from app.models.page_chunk import PageChunk


def search_chunks(query: str, limit: int = 5):
    embedder = EmbeddingModel()
    query_embedding = embedder.embed(query)

    db = SessionLocal()

    try:
        results = (
            db.query(PageChunk)
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