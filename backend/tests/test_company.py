import pytest

from fastapi import HTTPException
from unittest.mock import MagicMock

from fastapi import HTTPException

from app.models.user import User
from app.api.company import create_company, list_companies
from app.api.company import (
    create_company,
    delete_company,
    get_company,
    list_companies,
    update_company,
)

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

def test_get_company_for_user():
    db = MagicMock()

    company = MagicMock()
    company.id = 12
    company.name = "My Company"
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

    result = get_company(
        company_id=12,
        current_user=user,
        db=db,
    )

    assert result == {
        "id": 12,
        "name": "My Company",
        "website_url": "https://example.com",
    }

def test_get_company_rejects_unowned_company():
    db = MagicMock()

    (
        db.query.return_value
        .filter.return_value
        .first.return_value
    ) = None

    user = User(
        id=3,
        email="test@example.com",
        password_hash="unused",
    )

    try:
        get_company(
            company_id=1,
            current_user=user,
            db=db,
        )
        assert False, "Expected HTTPException"
    except HTTPException as error:
        assert error.status_code == 404
        assert error.detail == "Company not found"

def test_update_company_for_owner():
    db = MagicMock()

    company = MagicMock()
    company.id = 12
    company.name = "Old Name"
    company.website_url = "https://old.example.com"

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
    request.name = "New Name"
    request.website_url = "https://new.example.com"

    result = update_company(
        company_id=12,
        request=request,
        current_user=user,
        db=db,
    )

    assert company.name == "New Name"
    assert company.website_url == "https://new.example.com"

    assert result == {
        "id": 12,
        "name": "New Name",
        "website_url": "https://new.example.com",
    }

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(company)


def test_update_company_rejects_unowned_company():
    db = MagicMock()

    (
        db.query.return_value
        .filter.return_value
        .first.return_value
    ) = None

    user = User(
        id=3,
        email="test@example.com",
        password_hash="unused",
    )

    request = MagicMock()
    request.name = "Hacked Name"
    request.website_url = "https://hacked.example.com"

    with pytest.raises(HTTPException) as error:
        update_company(
            company_id=1,
            request=request,
            current_user=user,
            db=db,
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Company not found"


def test_delete_company_for_owner():
    db = MagicMock()

    company = MagicMock()
    company.id = 12
    company.owner_id = 3

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

    result = delete_company(
        company_id=12,
        current_user=user,
        db=db,
    )

    db.delete.assert_called_once_with(company)
    db.commit.assert_called_once()

    assert result == {
        "message": "Company deleted successfully",
        "company_id": 12,
    }

def test_delete_company_rejects_unowned_company():
    db = MagicMock()

    (
        db.query.return_value
        .filter.return_value
        .first.return_value
    ) = None

    user = User(
        id=3,
        email="test@example.com",
        password_hash="unused",
    )

    with pytest.raises(HTTPException) as error:
        delete_company(
            company_id=1,
            current_user=user,
            db=db,
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Company not found"

    db.delete.assert_not_called()
    db.commit.assert_not_called()