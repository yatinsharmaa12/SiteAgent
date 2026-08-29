from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.api.auth import login
from app.core.security import hash_password


def test_login_with_correct_password():
    user = MagicMock()
    user.id = 3
    user.email = "test@example.com"
    user.password_hash = hash_password("test-password-123")

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user

    with patch(
        "app.api.auth.create_access_token",
        return_value="fake-token",
    ):
        request = MagicMock()
        request.email = "test@example.com"
        request.password = "test-password-123"

        result = login(
            request=request,
            db=db,
        )

    assert result == {
        "access_token": "fake-token",
        "token_type": "bearer",
    }


def test_login_with_wrong_password():
    user = MagicMock()
    user.id = 3
    user.email = "test@example.com"
    user.password_hash = hash_password("correct-password")

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user

    request = MagicMock()
    request.email = "test@example.com"
    request.password = "wrong-password"

    try:
        login(
            request=request,
            db=db,
        )
        assert False, "Expected HTTPException"
    except HTTPException as error:
        assert error.status_code == 401
        assert error.detail == "Invalid email or password"