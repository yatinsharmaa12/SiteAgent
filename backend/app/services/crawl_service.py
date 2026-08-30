from datetime import datetime

from app.crawler.crawler import crawl_site
from app.db.database import SessionLocal
from app.models.crawl_job import CrawlJob
from app.repositories.company_repository import get_company


async def run_crawl_job(
    job_id: int,
    company_id: int,
):
    db = SessionLocal()

    try:
        job = (
            db.query(CrawlJob)
            .filter(
                CrawlJob.id == job_id,
                CrawlJob.company_id == company_id,
            )
            .first()
        )

        if not job:
            return

        company = get_company(
            db=db,
            company_id=company_id,
        )

        if not company:
            job.status = "FAILED"
            job.error = "Company not found"
            job.completed_at = datetime.utcnow()
            db.commit()
            return

        job.status = "RUNNING"
        job.started_at = datetime.utcnow()

        job.pages_discovered = 0
        job.pages_crawled = 0
        job.pages_indexed = 0
        job.pages_failed = 0

        db.commit()

        try:
            pages, _ = await crawl_site(
                company.website_url,
                db=db,
                company_id=company.id,
                max_pages=job.max_pages,
                max_depth=job.max_depth,
                crawl_job=job,
            )

            job.pages_crawled = len(pages)

            job.status = "COMPLETED"
            job.completed_at = datetime.utcnow()

            db.commit()

        except Exception as error:
            job.status = "FAILED"
            job.error = str(error)
            job.completed_at = datetime.utcnow()

            db.commit()

    finally:
        db.close()