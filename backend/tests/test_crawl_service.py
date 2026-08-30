from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.crawl_service import run_crawl_job


@pytest.mark.anyio
async def test_run_crawl_job_completes():
    db = MagicMock()

    job = MagicMock()
    job.id = 99
    job.company_id = 12
    job.max_pages = 5
    job.max_depth = 1

    company = MagicMock()
    company.id = 12
    company.website_url = "https://example.com"

    (
        db.query.return_value
        .filter.return_value
        .first.return_value
    ) = job

    with patch(
        "app.services.crawl_service.SessionLocal",
        return_value=db,
    ), patch(
        "app.services.crawl_service.get_company",
        return_value=company,
    ), patch(
        "app.services.crawl_service.crawl_site",
        new_callable=AsyncMock,
        return_value=([], MagicMock()),
    ) as mock_crawl:

        await run_crawl_job(
            job_id=99,
            company_id=12,
        )

    assert job.status == "COMPLETED"
    assert job.pages_crawled == 0
    assert job.completed_at is not None

    mock_crawl.assert_awaited_once_with(
        "https://example.com",
        db=db,
        company_id=12,
        max_pages=5,
        max_depth=1,
    )

    db.commit.assert_called()
    db.close.assert_called_once()

@pytest.mark.anyio
async def test_run_crawl_job_marks_failed():
    db = MagicMock()

    job = MagicMock()
    job.id = 99
    job.company_id = 12
    job.max_pages = 5
    job.max_depth = 1

    company = MagicMock()
    company.id = 12
    company.website_url = "https://example.com"

    (
        db.query.return_value
        .filter.return_value
        .first.return_value
    ) = job

    with patch(
        "app.services.crawl_service.SessionLocal",
        return_value=db,
    ), patch(
        "app.services.crawl_service.get_company",
        return_value=company,
    ), patch(
        "app.services.crawl_service.crawl_site",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Crawler crashed"),
    ):

        await run_crawl_job(
            job_id=99,
            company_id=12,
        )

    assert job.status == "FAILED"
    assert job.error == "Crawler crashed"
    assert job.completed_at is not None

    db.commit.assert_called()
    db.close.assert_called_once()