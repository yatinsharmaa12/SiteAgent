from unittest.mock import MagicMock

from app.repositories.company_repository import (
    get_company_for_user,
    list_companies_for_user,
)


def test_get_company_for_user():
    db = MagicMock()

    company = MagicMock()
    company.id = 12
    company.owner_id = 3

    (
        db.query.return_value
        .filter.return_value
        .first.return_value
    ) = company

    result = get_company_for_user(
        db=db,
        company_id=12,
        user_id=3,
    )

    assert result == company
    db.query.return_value.filter.assert_called_once()


def test_list_companies_for_user():
    db = MagicMock()

    companies = [
        MagicMock(id=12, owner_id=3),
        MagicMock(id=13, owner_id=3),
    ]

    (
        db.query.return_value
        .filter.return_value
        .order_by.return_value
        .all.return_value
    ) = companies

    result = list_companies_for_user(
        db=db,
        user_id=3,
    )

    assert result == companies
    db.query.return_value.filter.assert_called_once()