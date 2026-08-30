from unittest.mock import MagicMock

from app.repositories.crawl_job_repository import (
    create_crawl_job,
    get_crawl_job_for_company,
    list_crawl_jobs_for_company,
)


def test_create_crawl_job():
    db = MagicMock()

    result = create_crawl_job(
        db=db,
        company_id=13,
        max_pages=10,
        max_depth=2,
    )

    added_job = db.add.call_args[0][0]

    assert added_job.company_id == 13
    assert added_job.status == "QUEUED"
    assert added_job.max_pages == 10
    assert added_job.max_depth == 2
    assert added_job.pages_crawled == 0

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(added_job)

    assert result is added_job


def test_get_crawl_job_for_company():
    db = MagicMock()

    job = MagicMock()
    job.id = 7
    job.company_id = 13

    (
        db.query.return_value
        .filter.return_value
        .first.return_value
    ) = job

    result = get_crawl_job_for_company(
        db=db,
        job_id=7,
        company_id=13,
    )

    assert result is job

def test_list_crawl_jobs_for_company():
    db = MagicMock()

    jobs = [
        MagicMock(id=3, company_id=13),
        MagicMock(id=2, company_id=13),
    ]

    (
        db.query.return_value
        .filter.return_value
        .order_by.return_value
        .all.return_value
    ) = jobs

    result = list_crawl_jobs_for_company(
        db=db,
        company_id=13,
    )

    assert result == jobs