import logging
import os
from datetime import datetime

from redis import Redis
from rq import Queue
from rq.job import Retry


logger = logging.getLogger(__name__)

from app.db.database import SessionLocal
from app.domain.job_state import JobState, transition_job_state
from app.models.crawl_job import CrawlJob


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)

redis_connection = Redis.from_url(
    REDIS_URL,
)

crawl_queue = Queue(
    "crawl",
    connection=redis_connection,
)


def job_failure_handler(job, connection, type, value, traceback):
    """Called by RQ when a job fails or a worker crashes."""
    if not job.args:
        return
        
    job_id = job.args[0]
    logger.error("Worker/queue failure for crawl job %s: %s", job_id, value)
    db = SessionLocal()
    try:
        crawl_job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if crawl_job and crawl_job.status != JobState.COMPLETED.value:
            error_msg = f"Worker/Queue failure: {value}" if value else "Worker/Queue failure"
            transition_job_state(crawl_job, JobState.FAILED, error_msg)
            db.commit()
    finally:
        db.close()


def enqueue_crawl(
    job_id: int,
    company_id: int,
):

    return crawl_queue.enqueue(
        "app.services.crawl_service.run_crawl_job",
        job_id,
        company_id,
        on_failure=job_failure_handler,
        retry=Retry(
            max=3,
            interval=[10, 30, 60],
        ),
        job_timeout="30m",
    )