from unittest.mock import AsyncMock, patch

import pytest

from app.models.company import Company
from app.models.crawl_job import CrawlJob
from app.models.user import User
from app.services.crawl_service import run_crawl_job


@pytest.mark.anyio
async def test_run_crawl_job_completes_with_real_database(
    db,
    test_session_local,
):
    user = User(
        email="service-integration-complete@example.com",
        password_hash="unused",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    company = Company(
        name="Service Integration Company",
        website_url="https://example.com",
        owner_id=user.id,
    )

    db.add(company)
    db.commit()
    db.refresh(company)

    job = CrawlJob(
        company_id=company.id,
        status="QUEUED",
        max_pages=5,
        max_depth=1,
        pages_crawled=0,
        pages_new=7,
        pages_changed=6,
        pages_unchanged=5,
        pages_deactivated=4,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    with patch(
        "app.services.crawl_service.SessionLocal",
        test_session_local,
    ), patch(
        "app.services.crawl_service.crawl_site",
        new_callable=AsyncMock,
        return_value=([{"url": "https://example.com"}], None),
    ):
        await run_crawl_job(
            job_id=job.id,
            company_id=company.id,
        )

    db.expire_all()

    updated_job = (
        db.query(CrawlJob)
        .filter(CrawlJob.id == job.id)
        .first()
    )

    assert updated_job.status == "COMPLETED"
    assert updated_job.pages_crawled == 1
    assert updated_job.pages_new == 0
    assert updated_job.pages_changed == 0
    assert updated_job.pages_unchanged == 0
    assert updated_job.pages_deactivated == 0
    assert updated_job.started_at is not None
    assert updated_job.completed_at is not None
    assert updated_job.error is None


@pytest.mark.anyio
async def test_run_crawl_job_marks_failed_with_real_database(
    db,
    test_session_local,
):
    user = User(
        email="service-failure@example.com",
        password_hash="unused",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    company = Company(
        name="Service Failure Company",
        website_url="https://example.com",
        owner_id=user.id,
    )

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

    with patch(
        "app.services.crawl_service.SessionLocal",
        test_session_local,
    ), patch(
        "app.services.crawl_service.crawl_site",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Crawler crashed"),
    ):
        await run_crawl_job(
            job_id=job.id,
            company_id=company.id,
        )

    db.expire_all()

    updated_job = (
        db.query(CrawlJob)
        .filter(CrawlJob.id == job.id)
        .first()
    )

    assert updated_job.status == "FAILED"
    assert updated_job.error == "Crawler crashed"
    assert updated_job.started_at is not None
    assert updated_job.completed_at is not None
