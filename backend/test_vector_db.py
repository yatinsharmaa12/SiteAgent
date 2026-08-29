from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from app.models.page_db import Page
from app.db.database import SessionLocal
from app.models.page_chunk import PageChunk


model = SentenceTransformer("all-MiniLM-L6-v2")

text = "Redis is an in-memory database."

embedding = model.encode(text).tolist()

db = SessionLocal()

chunk = PageChunk(
    page_id=1,
    chunk_index=999,
    content=text,
    embedding=embedding,
)

db.add(chunk)
db.commit()
db.refresh(chunk)

print("Inserted ID:", chunk.id)
print("Embedding dimensions:", len(chunk.embedding))

db.close()