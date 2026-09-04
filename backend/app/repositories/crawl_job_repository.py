from sqlalchemy.orm import Session

from app.core.time import now_utc_naive
from app.models.crawl_job import CrawlJob


def create_crawl_job(
    db: Session,
    company_id: int,
    max_pages: int,
    max_depth: int,
):
    job = CrawlJob(
        company_id=company_id,
        status="QUEUED",
        max_pages=max_pages,
        max_depth=max_depth,
        pages_discovered=0,
        pages_crawled=0,
        pages_indexed=0,
        pages_failed=0,
        pages_new=0,
        pages_changed=0,
        pages_unchanged=0,
        pages_deactivated=0,
        created_at=now_utc_naive(),
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


def get_crawl_job_for_company(
    db: Session,
    job_id: int,
    company_id: int,
):
    return (
        db.query(CrawlJob)
        .filter(
            CrawlJob.id == job_id,
            CrawlJob.company_id == company_id,
        )
        .first()
    )


def list_crawl_jobs_for_company(
    db: Session,
    company_id: int,
):
    return (
        db.query(CrawlJob)
        .filter(
            CrawlJob.company_id == company_id,
        )
        .order_by(CrawlJob.id.desc())
        .all()
    )
