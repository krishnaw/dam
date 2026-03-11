"""Integration tests for auth API endpoints."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth import create_access_token, hash_password


class TestRegister:
    async def test_register_user(self, client):
        resp = await client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client):
        email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": email,
            "password": "securepassword123",
            "full_name": "First User",
        }
        # Register first time
        resp1 = await client.post("/api/auth/register", json=payload)
        assert resp1.status_code == 201

        # Register second time with same email
        resp2 = await client.post("/api/auth/register", json=payload)
        assert resp2.status_code == 409

    async def test_register_short_password(self, client):
        resp = await client.post(
            "/api/auth/register",
            json={
                "email": "short@example.com",
                "password": "short",
                "full_name": "Short Pass",
            },
        )
        assert resp.status_code == 422  # validation error


class TestLogin:
    async def test_login_success(self, client):
        email = f"login-{uuid.uuid4().hex[:8]}@example.com"
        # Register
        await client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "securepassword123",
                "full_name": "Login User",
            },
        )
        # Login
        resp = await client.post(
            "/api/auth/login",
            json={"email": email, "password": "securepassword123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client):
        email = f"wrongpw-{uuid.uuid4().hex[:8]}@example.com"
        await client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "securepassword123",
                "full_name": "Test",
            },
        )
        resp = await client.post(
            "/api/auth/login",
            json={"email": email, "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client):
        resp = await client.post(
            "/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "password123"},
        )
        assert resp.status_code == 401


class TestGetMe:
    async def test_get_me_with_token(self, client):
        email = f"me-{uuid.uuid4().hex[:8]}@example.com"
        reg_resp = await client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "securepassword123",
                "full_name": "Me User",
            },
        )
        token = reg_resp.json()["access_token"]

        resp = await client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == email
        assert data["full_name"] == "Me User"

    async def test_access_without_token(self, client):
        resp = await client.get("/api/users/me")
        assert resp.status_code in (401, 403)  # HTTPBearer may return 401 or 403


class TestRBACViewer:
    """Test that viewers cannot perform editor/manager actions."""

    async def test_rbac_viewer_cannot_upload(self, client, make_auth_headers):
        headers, _ = make_auth_headers(role="viewer")
        resp = await client.post(
            "/api/assets/upload",
            headers=headers,
            files={"file": ("test.txt", b"hello", "text/plain")},
        )
        assert resp.status_code == 403

    async def test_rbac_viewer_cannot_delete(self, client, make_auth_headers):
        headers, _ = make_auth_headers(role="viewer")
        fake_id = str(uuid.uuid4())
        resp = await client.delete(
            f"/api/assets/{fake_id}",
            headers=headers,
        )
        assert resp.status_code == 403

    async def test_rbac_viewer_cannot_create_collection(self, client, make_auth_headers):
        headers, _ = make_auth_headers(role="viewer")
        resp = await client.post(
            "/api/collections/",
            headers=headers,
            json={"name": "Test Collection"},
        )
        assert resp.status_code == 403

    async def test_rbac_viewer_cannot_create_share(self, client, make_auth_headers):
        headers, _ = make_auth_headers(role="viewer")
        resp = await client.post(
            "/api/shares/",
            headers=headers,
            json={"asset_id": str(uuid.uuid4())},
        )
        assert resp.status_code == 403


class TestRBACEditor:
    """Test that editors can perform editor actions but not manager actions."""

    async def test_rbac_editor_cannot_delete_asset(self, client, make_auth_headers):
        headers, _ = make_auth_headers(role="editor")
        fake_id = str(uuid.uuid4())
        resp = await client.delete(
            f"/api/assets/{fake_id}",
            headers=headers,
        )
        assert resp.status_code == 403

    async def test_rbac_editor_cannot_delete_collection(self, client, make_auth_headers):
        headers, _ = make_auth_headers(role="editor")
        fake_id = str(uuid.uuid4())
        resp = await client.delete(
            f"/api/collections/{fake_id}",
            headers=headers,
        )
        assert resp.status_code == 403


class TestRBACAdmin:
    async def test_rbac_admin_can_list_users(self, client, make_auth_headers):
        headers, _ = make_auth_headers(role="admin")
        resp = await client.get("/api/users", headers=headers)
        assert resp.status_code == 200

    async def test_rbac_non_admin_cannot_list_users(self, client, make_auth_headers):
        headers, _ = make_auth_headers(role="editor")
        resp = await client.get("/api/users", headers=headers)
        assert resp.status_code == 403


class TestGoogleOAuth:
    async def test_google_login_returns_url(self, client):
        # google/login endpoint does not require auth
        resp = await client.get("/api/auth/google/login")
        assert resp.status_code == 200
        data = resp.json()
        assert "url" in data
        assert "accounts.google.com" in data["url"]

    @patch("app.api.users.verify_google_token", new_callable=AsyncMock)
    async def test_google_callback_creates_user(
        self, mock_verify, client, db_session
    ):
        mock_verify.return_value = {
            "id": "google-123456",
            "email": "googleuser@gmail.com",
            "name": "Google User",
            "picture": "https://example.com/photo.jpg",
        }

        resp = await client.post(
            "/api/auth/google/callback",
            json={"code": "fake-auth-code"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

        # Verify user was created in DB
        result = await db_session.execute(
            select(User).where(User.email == "googleuser@gmail.com")
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.google_id == "google-123456"
        assert user.full_name == "Google User"
        assert user.role.value == "viewer"
        assert user.hashed_password is None

    async def test_google_callback_invalid_code(self, client):
        # Without mocking, this should fail since the code is invalid
        resp = await client.post(
            "/api/auth/google/callback",
            json={"code": "invalid-code"},
        )
        assert resp.status_code == 400
