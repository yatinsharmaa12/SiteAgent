from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.company_crawl import crawl_company
from app.models.user import User


@pytest.mark.anyio
async def test_company_owner_can_crawl():
    db = MagicMock()

    company = MagicMock()
    company.id = 12
    company.name = "Test Company"
    company.website_url = "https://example.com"

    (
        db.query.return_value
        .filter.return_value
        .first.return_value
    ) = company

    user = User(
        id=3,
        email="test@example.com",
        password_hash="unused",
    )

    request = MagicMock()
    request.max_pages = 5
    request.max_depth = 1

    with patch(
        "app.api.company_crawl.crawl_site",
        new_callable=AsyncMock,
        return_value=([], MagicMock()),
    ) as mock_crawl:

        mock_crawl.return_value[1].all.return_value = []

        result = await crawl_company(
            company_id=12,
            request=request,
            current_user=user,
            db=db,
        )

    assert result["company_id"] == 12
    assert result["company_name"] == "Test Company"
    assert result["start_url"] == "https://example.com"

    mock_crawl.assert_awaited_once_with(
        "https://example.com",
        db=db,
        company_id=12,
        max_pages=5,
        max_depth=1,
    )


@pytest.mark.anyio
async def test_company_owner_cannot_crawl_unowned_company():
    db = MagicMock()

    user = User(
        id=3,
        email="test@example.com",
        password_hash="unused",
    )

    request = MagicMock()
    request.max_pages = 5
    request.max_depth = 1

    with patch(
        "app.api.company_crawl.get_company_for_user",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as error:
            await crawl_company(
                company_id=1,
                request=request,
                current_user=user,
                db=db,
            )

    assert error.value.status_code == 404
    assert error.value.detail == "Company not found"

def test_company_crawl_requires_authentication():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    response = client.post(
        "/companies/12/crawl",
        json={
            "max_pages": 1,
            "max_depth": 0,
        },
    )

    assert response.status_code == 401