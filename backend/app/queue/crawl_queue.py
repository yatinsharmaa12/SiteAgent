import os

from redis import Redis
from rq import Queue


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

def enqueue_crawl(
    job_id: int,
    company_id: int,
):
    return crawl_queue.enqueue(
        "app.services.crawl_service.run_crawl_job",
        job_id,
        company_id,
    )