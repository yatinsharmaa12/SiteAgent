from enum import Enum
from datetime import datetime


class JobState(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class InvalidStateTransition(Exception):
    pass


VALID_TRANSITIONS = {
    JobState.QUEUED: {JobState.RUNNING, JobState.FAILED, JobState.CANCELLED},
    JobState.RUNNING: {JobState.COMPLETED, JobState.FAILED, JobState.QUEUED, JobState.CANCELLED},
    JobState.COMPLETED: set(),
    JobState.FAILED: set(),
    JobState.CANCELLED: set(),
    JobState.TIMED_OUT: set(),
}


def transition_job_state(job, new_status: str, error: str = None):
    current_status = JobState(job.status)
    new_state = JobState(new_status)
    
    if new_state not in VALID_TRANSITIONS[current_status]:
        raise InvalidStateTransition(
            f"Cannot transition from {current_status.value} to {new_state.value}"
        )
        
    job.status = new_state.value
    
    if new_state == JobState.RUNNING:
        if current_status == JobState.QUEUED:
            job.attempt_count += 1
        job.started_at = datetime.utcnow()
        job.last_heartbeat_at = datetime.utcnow()
    elif new_state == JobState.COMPLETED:
        job.completed_at = datetime.utcnow()
    elif new_state in {JobState.FAILED, JobState.CANCELLED, JobState.TIMED_OUT}:
        job.completed_at = datetime.utcnow()
        if error:
            job.error = error
    elif new_state == JobState.QUEUED and current_status == JobState.RUNNING:
        # Retryable failure resets back to QUEUED
        if error:
            job.error = error
