import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.models.company import Company
from app.models.crawl_job import CrawlJob
from app.models.page import Page
from app.models.user import User
from app.services.crawl_service import run_crawl_job
from app.models.url import URLStatus
from app.models.url_db import URL

# Helper to get URL record from DB
def get_url_record(db, company_id, url):
    return (
        db.query(URL)
        .filter(URL.company_id == company_id, URL.normalized_url == url)
        .first()
    )

@pytest.mark.anyio
async def test_incremental_crawl_unchanged_content(db, test_session_local):
    # Setup user, company, and crawl job
    user = User(email="inc-test@example.com", password_hash="unused")
    db.add(user)
    db.commit()
    db.refresh(user)

    company = Company(name="Inc Test Co", website_url="https://example.com", owner_id=user.id)
    db.add(company)
    db.commit()
    db.refresh(company)

    job = CrawlJob(
        company_id=company.id,
        status="QUEUED",
        max_pages=5,
        max_depth=1,
        pages_crawled=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    async def mock_fetch_page(url):
        return "<html><body>content v1</body></html>", 200

    with patch(
        "app.services.crawl_service.SessionLocal", test_session_local
    ), patch(
        "app.services.crawl_service.get_company", return_value=company
    ), patch(
        "app.crawler.fetcher.fetch_page", new_callable=AsyncMock, side_effect=mock_fetch_page
    ):
        await run_crawl_job(job_id=job.id, company_id=company.id)

    db.expire_all()
    page = db.query(Page).filter(Page.company_id == company.id).first()
    assert page is not None
    assert page.content == "content v1"
    url_rec = get_url_record(db, company.id, "https://example.com")
    assert url_rec.status == URLStatus.INDEXED.value
    assert url_rec.last_seen_at is not None
    first_seen = url_rec.last_seen_at

    async def mock_fetch_same(url):
        return "<html><body>content v1</body></html>", 200

    with patch(
        "app.services.crawl_service.SessionLocal", test_session_local
    ), patch(
        "app.services.crawl_service.get_company", return_value=company
    ), patch(
        "app.crawler.fetcher.fetch_page", new_callable=AsyncMock, side_effect=mock_fetch_same
    ):
        await run_crawl_job(job_id=job.id, company_id=company.id)

    db.expire_all()
    page_count = db.query(Page).filter(Page.company_id == company.id).count()
    assert page_count == 1
    url_rec2 = get_url_record(db, company.id, "https://example.com")
    assert url_rec2.last_seen_at > first_seen
    assert url_rec2.status == URLStatus.INDEXED.value

@pytest.mark.anyio
async def test_deactivate_unseen_urls(db, test_session_local):
    # Setup user, company, and crawl job with depth 0 so a discovered link is not visited
    user = User(email="deact-test@example.com", password_hash="unused")
    db.add(user)
    db.commit()
    db.refresh(user)

    company = Company(name="Deact Co", website_url="https://example.com", owner_id=user.id)
    db.add(company)
    db.commit()
    db.refresh(company)

    job = CrawlJob(
        company_id=company.id,
        status="QUEUED",
        max_pages=5,
        max_depth=0,
        pages_crawled=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    async def mock_fetch(url):
        return "<html><body>root</body></html>", 200

    with patch(
        "app.services.crawl_service.SessionLocal", test_session_local
    ), patch(
        "app.services.crawl_service.get_company", return_value=company
    ), patch(
        "app.crawler.fetcher.fetch_page", new_callable=AsyncMock, side_effect=mock_fetch
    ), patch(
        "app.crawler.crawler.extract_links", return_value=["https://example.com/unused"]
    ):
        await run_crawl_job(job_id=job.id, company_id=company.id)

    db.expire_all()
    unused_url = get_url_record(db, company.id, "https://example.com/unused")
    assert unused_url is not None
    assert unused_url.status == URLStatus.DEACTIVATED.value
    assert unused_url.is_active is True
