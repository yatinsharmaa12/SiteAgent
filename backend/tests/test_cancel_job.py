import pytest
from app.domain.job_state import JobState, InvalidStateTransition, transition_job_state
from app.services.crawl_service import cancel_crawl_job


def test_cancel_queued_job():
    class MockJob:
        def __init__(self, status):
            self.status = status
            self.started_at = None
            self.completed_at = None
            self.last_heartbeat_at = None
            self.error = None
            self.attempt_count = 0
            
    job = MockJob(JobState.QUEUED.value)
    transition_job_state(job, JobState.CANCELLED, "Cancelled")
    
    assert job.status == JobState.CANCELLED.value
    assert job.completed_at is not None


def test_cancel_running_job():
    class MockJob:
        def __init__(self, status):
            self.status = status
            self.started_at = None
            self.completed_at = None
            self.last_heartbeat_at = None
            self.error = None
            self.attempt_count = 1
            
    job = MockJob(JobState.RUNNING.value)
    transition_job_state(job, JobState.CANCELLED, "Cancelled")
    
    assert job.status == JobState.CANCELLED.value
    assert job.completed_at is not None


def test_cannot_cancel_completed_job():
    class MockJob:
        def __init__(self, status):
            self.status = status
            self.started_at = None
            self.completed_at = None
            self.last_heartbeat_at = None
            self.error = None
            self.attempt_count = 1
            
    job = MockJob(JobState.COMPLETED.value)
    
    with pytest.raises(InvalidStateTransition):
        transition_job_state(job, JobState.CANCELLED, "Cancelled")
