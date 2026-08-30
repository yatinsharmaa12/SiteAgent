from unittest.mock import MagicMock, patch

from app.queue.crawl_queue import job_failure_handler


def test_job_failure_handler():
    job = MagicMock()
    job.args = [99, 12]

    db = MagicMock()
    
    crawl_job = MagicMock()
    crawl_job.id = 99
    crawl_job.status = "QUEUED"
    
    (
        db.query.return_value
        .filter.return_value
        .first.return_value
    ) = crawl_job

    with patch("app.queue.crawl_queue.SessionLocal", return_value=db):
        job_failure_handler(
            job=job,
            connection=None,
            type=RuntimeError,
            value=RuntimeError("Worker died"),
            traceback=None,
        )

    assert crawl_job.status == "FAILED"
    assert "Worker died" in crawl_job.error
    assert crawl_job.completed_at is not None
    db.commit.assert_called_once()
    db.close.assert_called_once()


def test_job_failure_handler_ignores_completed_job():
    job = MagicMock()
    job.args = [99, 12]

    db = MagicMock()
    
    crawl_job = MagicMock()
    crawl_job.id = 99
    crawl_job.status = "COMPLETED"
    
    (
        db.query.return_value
        .filter.return_value
        .first.return_value
    ) = crawl_job

    with patch("app.queue.crawl_queue.SessionLocal", return_value=db):
        job_failure_handler(
            job=job,
            connection=None,
            type=RuntimeError,
            value=RuntimeError("Worker died"),
            traceback=None,
        )

    assert crawl_job.status == "COMPLETED"
    db.commit.assert_not_called()
    db.close.assert_called_once()


def test_job_failure_handler_no_args():
    job = MagicMock()
    job.args = []
    
    with patch("app.queue.crawl_queue.SessionLocal") as mock_session:
        job_failure_handler(
            job=job,
            connection=None,
            type=RuntimeError,
            value=RuntimeError("Worker died"),
            traceback=None,
        )
    
    mock_session.assert_not_called()
