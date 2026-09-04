import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock

from app.core.time import now_utc_naive

from app.services.recovery_service import recover_stale_jobs
from app.domain.job_state import JobState


class MockCrawlJob:
    def __init__(self, id, status, heartbeat_offset=0):
        self.id = id
        self.status = status
        self.created_at = now_utc_naive() - timedelta(seconds=1000)
        self.started_at = now_utc_naive() - timedelta(seconds=500)

        if heartbeat_offset is not None:
            self.last_heartbeat_at = now_utc_naive() - timedelta(seconds=heartbeat_offset)
        else:
            self.last_heartbeat_at = None
            
        self.completed_at = None
        self.error = None


def setup_mock_db(jobs):
    db = MagicMock()
    # When query().filter().all() is called, return the jobs
    db.query.return_value.filter.return_value.all.return_value = [j for j in jobs if j.status == JobState.RUNNING.value]
    
    # Simple db.refresh mock
    def mock_refresh(job):
        pass
    db.refresh = mock_refresh
    
    return db


def test_recovery_service_ignores_fresh_heartbeat():
    job = MockCrawlJob(1, JobState.RUNNING.value, heartbeat_offset=10) # 10 seconds ago
    db = setup_mock_db([job])
    
    with patch("app.services.recovery_service.SessionLocal", return_value=db):
        recovered = recover_stale_jobs(timeout_seconds=300)
        
    assert recovered == 0
    assert job.status == JobState.RUNNING.value


def test_recovery_service_recovers_stale_heartbeat():
    job = MockCrawlJob(2, JobState.RUNNING.value, heartbeat_offset=400) # 400 seconds ago
    db = setup_mock_db([job])
    
    with patch("app.services.recovery_service.SessionLocal", return_value=db):
        recovered = recover_stale_jobs(timeout_seconds=300)
        
    assert recovered == 1
    assert job.status == JobState.FAILED.value
    assert "Worker heartbeat timeout" in job.error


def test_recovery_service_recovers_stale_started_at_if_no_heartbeat():
    job = MockCrawlJob(3, JobState.RUNNING.value, heartbeat_offset=None)
    # created_at and started_at are 1000s and 500s ago
    db = setup_mock_db([job])
    
    with patch("app.services.recovery_service.SessionLocal", return_value=db):
        recovered = recover_stale_jobs(timeout_seconds=300)
        
    assert recovered == 1
    assert job.status == JobState.FAILED.value


def test_recovery_service_ignores_completed_and_failed_jobs():
    job1 = MockCrawlJob(4, JobState.COMPLETED.value, heartbeat_offset=400)
    job2 = MockCrawlJob(5, JobState.FAILED.value, heartbeat_offset=400)
    job3 = MockCrawlJob(6, JobState.QUEUED.value, heartbeat_offset=400)
    db = setup_mock_db([job1, job2, job3])
    
    with patch("app.services.recovery_service.SessionLocal", return_value=db):
        recovered = recover_stale_jobs(timeout_seconds=300)
        
    assert recovered == 0


def test_recovery_service_is_idempotent():
    job = MockCrawlJob(7, JobState.RUNNING.value, heartbeat_offset=400)
    db = setup_mock_db([job])
    
    with patch("app.services.recovery_service.SessionLocal", return_value=db):
        recovered1 = recover_stale_jobs(timeout_seconds=300)
        
    assert recovered1 == 1
    assert job.status == JobState.FAILED.value
    
    # If we run it again, the job is no longer RUNNING (it's FAILED), so it won't be fetched
    db = setup_mock_db([job]) 
    with patch("app.services.recovery_service.SessionLocal", return_value=db):
        recovered2 = recover_stale_jobs(timeout_seconds=300)
        
    assert recovered2 == 0
