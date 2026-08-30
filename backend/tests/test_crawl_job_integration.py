from datetime import datetime

from app.models.company import Company
from app.models.crawl_job import CrawlJob
from app.models.user import User


def test_crawl_job_state_transition(db):
    user = User(
        email="state-transition@example.com",
        password_hash="unused",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    company = Company(
        name="State Test Company",
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

    assert job.status == "QUEUED"

    job.status = "RUNNING"
    job.started_at = datetime.utcnow()

    db.commit()
    db.refresh(job)

    assert job.status == "RUNNING"
    assert job.started_at is not None

    job.status = "COMPLETED"
    job.pages_crawled = 3
    job.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(job)

    assert job.status == "COMPLETED"
    assert job.pages_crawled == 3
    assert job.completed_at is not None