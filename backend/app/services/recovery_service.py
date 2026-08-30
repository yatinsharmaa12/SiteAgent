from datetime import datetime, timedelta

from app.db.database import SessionLocal
from app.models.crawl_job import CrawlJob
from app.domain.job_state import JobState, transition_job_state


def recover_stale_jobs(timeout_seconds: int = 300) -> int:
    """
    Finds RUNNING jobs with stale heartbeats and marks them FAILED.
    """
    db = SessionLocal()
    recovered_count = 0
    try:
        threshold_time = datetime.utcnow() - timedelta(seconds=timeout_seconds)
        
        # Initial fast fetch of potentially stale jobs
        stale_jobs = (
            db.query(CrawlJob)
            .filter(CrawlJob.status == JobState.RUNNING.value)
            .all()
        )
        
        for job in stale_jobs:
            # Refresh to ensure we have the absolute latest heartbeat before transitioning
            db.refresh(job)
            
            stale_time = job.last_heartbeat_at or job.started_at or job.created_at
            
            if stale_time < threshold_time and job.status == JobState.RUNNING.value:
                transition_job_state(
                    job, 
                    JobState.FAILED, 
                    f"Worker heartbeat timeout (stale for > {timeout_seconds}s)"
                )
                db.commit()
                recovered_count += 1
                
    finally:
        db.close()
        
    return recovered_count
