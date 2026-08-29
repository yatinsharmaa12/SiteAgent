from unittest.mock import MagicMock

from app.models.user import User
from app.api.company import create_company, list_companies

def test_create_company_assigns_current_user():
    db = MagicMock()

    user = User(
        id=3,
        email="test@example.com",
        password_hash="unused",
    )

    request = MagicMock()
    request.name = "Test Company"
    request.website_url = "https://example.com"

    result = create_company(
        request=request,
        current_user=user,
        db=db,
    )

    assert result["name"] == "Test Company"
    assert result["website_url"] == "https://example.com"

    created_company = db.add.call_args.args[0]

    assert created_company.owner_id == 3
    assert created_company.name == "Test Company"
    assert created_company.website_url == "https://example.com"

def test_list_companies_only_returns_owned_companies():
    db = MagicMock()

    owned_company = MagicMock()
    owned_company.id = 12
    owned_company.name = "My Company"
    owned_company.website_url = "https://example.com"

    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
        owned_company
    ]

    user = User(
        id=3,
        email="test@example.com",
        password_hash="unused",
    )

    result = list_companies(
        current_user=user,
        db=db,
    )

    assert result == [
        {
            "id": 12,
            "name": "My Company",
            "website_url": "https://example.com",
        }
    ]

    db.query.return_value.filter.assert_called_once()