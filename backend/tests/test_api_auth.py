from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_requires_authentication():
    response = client.post(
        "/chat",
        json={
            "company_id": 12,
            "question": "What fields are available?",
        },
    )

    assert response.status_code == 401


def test_crawl_requires_authentication():
    response = client.post(
        "/companies/12/crawl",
        json={
            "max_pages": 1,
            "max_depth": 0,
        },
    )

    assert response.status_code == 401

def test_delete_company_requires_authentication():
    response = client.delete(
        "/companies/12",
    )

    assert response.status_code == 401

def test_get_crawl_job_requires_authentication():
    response = client.get(
        "/companies/12/crawl-jobs/99",
    )

    assert response.status_code == 401

def test_list_crawl_jobs_requires_authentication():
    response = client.get(
        "/companies/12/crawl-jobs",
    )

    assert response.status_code == 401