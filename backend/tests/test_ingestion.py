from unittest.mock import Mock

from app.ingestion.ingest import ingest_page
from app.models.company import Company
from app.models.page_chunk import PageChunk
from app.models.page_db import Page
from app.models.url_db import URL
from app.models.user import User


def test_ingest_page_creates_chunks(db):
    # User
    user = User(
        email="ingestion-test@example.com",
        password_hash="unused",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Company
    company = Company(
        name="Ingestion Test Company",
        website_url="https://example.com",
        owner_id=user.id,
    )

    db.add(company)
    db.commit()
    db.refresh(company)

    # URL
    url = URL(
        company_id=company.id,
        url="https://example.com",
        normalized_url="https://example.com",
        status="QUEUED",
        depth=0,
    )

    db.add(url)
    db.commit()
    db.refresh(url)

    # Page
    page = Page(
        company_id=company.id,
        url_id=url.id,
        url="https://example.com",
        title="Test Page",
        content="This is test content for ingestion.",
        http_status=200,
        content_hash="test-hash",
    )

    db.add(page)
    db.commit()
    db.refresh(page)

    # Fake embedder
    fake_embedder = Mock()

    fake_embedder.embed_many.return_value = [
        [0.1] * 384,
    ]

    # Run ingestion
    ingest_page(
        page_id=page.id,
        db=db,
        embedder=fake_embedder,
    )

    # Check database
    chunks = (
        db.query(PageChunk)
        .filter(PageChunk.page_id == page.id)
        .all()
    )

    assert len(chunks) == 1
    assert chunks[0].page_id == page.id
    assert chunks[0].chunk_index == 0
    assert chunks[0].content
    assert len(chunks[0].embedding) == 384

    fake_embedder.embed_many.assert_called_once()