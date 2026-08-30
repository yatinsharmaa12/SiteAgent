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


def _make_page(db, email_suffix):
    """Helper: create a User, Company, URL, and Page in the test DB."""
    user = User(email=f"ing-{email_suffix}@example.com", password_hash="unused")
    db.add(user)
    db.commit()
    db.refresh(user)

    company = Company(name=f"Co {email_suffix}", website_url="https://example.com", owner_id=user.id)
    db.add(company)
    db.commit()
    db.refresh(company)

    url = URL(
        company_id=company.id,
        url="https://example.com",
        normalized_url="https://example.com",
        status="queued",
        depth=0,
    )
    db.add(url)
    db.commit()
    db.refresh(url)

    page = Page(
        company_id=company.id,
        url_id=url.id,
        url="https://example.com",
        title="Test",
        content="Some content long enough to produce a chunk for testing purposes.",
        http_status=200,
        content_hash="hash-v1",
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


def test_reingest_replace_existing_no_duplicates(db):
    """Calling ingest_page with replace_existing=True must replace, not accumulate, chunks."""
    page = _make_page(db, "nodup")

    fake_embedder = Mock()
    fake_embedder.embed_many.return_value = [[0.1] * 384]

    # First ingest
    ingest_page(page.id, db=db, embedder=fake_embedder)
    count_after_first = db.query(PageChunk).filter(PageChunk.page_id == page.id).count()
    assert count_after_first == 1

    # Re-ingest with replace_existing (simulates changed-page path)
    ingest_page(page.id, db=db, embedder=fake_embedder, replace_existing=True)
    count_after_second = db.query(PageChunk).filter(PageChunk.page_id == page.id).count()

    # Must still be exactly the same count, not doubled
    assert count_after_second == count_after_first


def test_ingest_without_replace_existing_does_not_duplicate(db):
    """Calling ingest_page twice without replace_existing must not create duplicates."""
    page = _make_page(db, "nodup2")

    fake_embedder = Mock()
    fake_embedder.embed_many.return_value = [[0.1] * 384]

    ingest_page(page.id, db=db, embedder=fake_embedder)
    ingest_page(page.id, db=db, embedder=fake_embedder)  # second call, no replace

    count = db.query(PageChunk).filter(PageChunk.page_id == page.id).count()
    assert count == 1  # guard against duplicates