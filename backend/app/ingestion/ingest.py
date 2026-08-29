from app.db.database import SessionLocal
from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import chunk_text
from app.ingestion.embedding import EmbeddingModel
from app.models.page_db import Page
from app.models.page_chunk import PageChunk


def ingest_page(page_id: int):
    db = SessionLocal()

    try:
        page = db.query(Page).filter(Page.id == page_id).first()

        if page is None:
            raise ValueError(f"Page {page_id} not found")

        existing_chunks = (
            db.query(PageChunk)
            .filter(PageChunk.page_id == page.id)
            .count()
        )

        if existing_chunks > 0:
            print(f"Page {page.id} already ingested")
            return

        cleaned = clean_text(page.content)

        chunks = chunk_text(
            cleaned,
            chunk_size=500,
        )

        embedder = EmbeddingModel()

        embeddings = embedder.embed_many(chunks)

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):
            page_chunk = PageChunk(
                page_id=page.id,
                chunk_index=index,
                content=chunk,
                embedding=embedding,
            )

            db.add(page_chunk)

        db.commit()

        print(
            f"Ingested Page {page.id}: "
            f"{len(chunks)} chunks"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

