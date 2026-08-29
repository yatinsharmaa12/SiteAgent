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
        "/crawl",
        json={
            "url": "https://example.com",
            "max_pages": 1,
            "max_depth": 0,
        },
    )

    assert response.status_code == 401