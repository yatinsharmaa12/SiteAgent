from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.dependencies import get_current_user
from app.main import app
from app.models.user import User


client = TestClient(app)


def test_crawl_returns_queued_job():
    user = User(
        id=3,
        email="test@example.com",
        password_hash="unused",
    )

    company = MagicMock()
    company.id = 12
    company.name = "Test Company"
    company.website_url = "https://example.com"

    job = MagicMock()
    job.id = 123
    job.status = "QUEUED"

    app.dependency_overrides[get_current_user] = lambda: user

    try:
        with patch(
            "app.api.company_crawl.get_company_for_user",
            return_value=company,
        ), patch(
            "app.api.company_crawl.create_crawl_job",
            return_value=job,
        ), patch(
            "app.api.company_crawl.enqueue_crawl",
        ):

            response = client.post(
                "/companies/12/crawl",
                json={
                    "max_pages": 5,
                    "max_depth": 1,
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["job_id"] == 123
        assert data["company_id"] == 12
        assert data["company_name"] == "Test Company"
        assert data["start_url"] == "https://example.com"
        assert data["status"] == "QUEUED"

        assert "pages" not in data
        assert "url_registry" not in data

    finally:
        app.dependency_overrides.clear()