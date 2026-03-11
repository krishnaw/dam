"""Unit tests for auth service."""

import time
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from jose import jwt

from app.config import settings
from app.services.auth import (
    RoleChecker,
    create_access_token,
    create_refresh_token,
    hash_password,
    require_editor,
    require_manager,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    def test_hash_password_produces_bcrypt_string(self):
        hashed = hash_password("mysecretpassword")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        assert len(hashed) > 50

    def test_verify_password_correct(self):
        hashed = hash_password("correcthorse")
        assert verify_password("correcthorse", hashed) is True

    def test_verify_password_wrong(self):
        hashed = hash_password("correcthorse")
        assert verify_password("wrongpassword", hashed) is False

    def test_hash_password_different_each_time(self):
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2  # bcrypt uses random salt


class TestAccessToken:
    def test_create_access_token_contains_claims(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, role="editor")
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        assert payload["sub"] == str(user_id)
        assert payload["role"] == "editor"
        assert "exp" in payload

    def test_verify_token_valid(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, role="admin")
        payload = verify_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["role"] == "admin"

    def test_verify_token_expired(self):
        user_id = uuid.uuid4()
        expire = datetime.now(timezone.utc) - timedelta(minutes=5)
        payload = {"sub": str(user_id), "role": "viewer", "exp": expire}
        token = jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        assert exc_info.value.status_code == 401

    def test_verify_token_invalid(self):
        with pytest.raises(HTTPException) as exc_info:
            verify_token("not-a-valid-token")
        assert exc_info.value.status_code == 401

    def test_create_access_token_different_roles(self):
        user_id = uuid.uuid4()
        for role in ["admin", "manager", "editor", "reviewer", "viewer"]:
            token = create_access_token(user_id=user_id, role=role)
            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )
            assert payload["role"] == role


class TestRefreshToken:
    def test_create_refresh_token_is_hex_string(self):
        token = create_refresh_token()
        assert isinstance(token, str)
        assert len(token) == 128  # 64 bytes -> 128 hex chars
        int(token, 16)  # should not raise if valid hex

    def test_create_refresh_token_unique(self):
        tokens = {create_refresh_token() for _ in range(10)}
        assert len(tokens) == 10  # all unique


class TestRoleChecker:
    def test_role_checker_allows_admin(self):
        checker = RoleChecker(["admin", "manager", "editor"])
        user = {"sub": str(uuid.uuid4()), "role": "admin"}
        result = checker(user=user)
        assert result["role"] == "admin"

    def test_role_checker_blocks_viewer_from_editor_route(self):
        checker = RoleChecker(["admin", "manager", "editor"])
        user = {"sub": str(uuid.uuid4()), "role": "viewer"}
        with pytest.raises(HTTPException) as exc_info:
            checker(user=user)
        assert exc_info.value.status_code == 403

    def test_role_checker_blocks_unauthorized_role(self):
        checker = RoleChecker(["admin"])
        user = {"sub": str(uuid.uuid4()), "role": "editor"}
        with pytest.raises(HTTPException) as exc_info:
            checker(user=user)
        assert exc_info.value.status_code == 403

    def test_require_manager_allows_manager(self):
        user = {"sub": str(uuid.uuid4()), "role": "manager"}
        result = require_manager(user=user)
        assert result["role"] == "manager"

    def test_require_manager_blocks_editor(self):
        user = {"sub": str(uuid.uuid4()), "role": "editor"}
        with pytest.raises(HTTPException) as exc_info:
            require_manager(user=user)
        assert exc_info.value.status_code == 403
        assert "editor" in exc_info.value.detail
