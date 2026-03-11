"""Integration tests for sharing API endpoints."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest


class TestShareLinks:
    async def test_create_share_link(
        self, client, db_session, make_asset, make_auth_headers
    ):
        headers, user_id = make_auth_headers()
        asset = make_asset(created_by=user_id)
        db_session.add(asset)
        await db_session.flush()

        resp = await client.post(
            "/api/shares/",
            headers=headers,
            json={"asset_id": str(asset.id), "permissions": "view"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["asset_id"] == str(asset.id)
        assert data["permissions"] == "view"
        assert data["is_active"] is True
        assert data["access_count"] == 0
        assert "token" in data
        assert data["share_url"].startswith("/share/")

    async def test_access_share_valid_token(
        self, client, db_session, make_asset, make_auth_headers
    ):
        headers, user_id = make_auth_headers()
        asset = make_asset(created_by=user_id)
        db_session.add(asset)
        await db_session.flush()

        # Create share
        create_resp = await client.post(
            "/api/shares/",
            headers=headers,
            json={"asset_id": str(asset.id)},
        )
        token = create_resp.json()["token"]

        # Access share (no auth required)
        resp = await client.get(f"/api/shares/{token}/access")
        assert resp.status_code == 200
        data = resp.json()
        assert data["asset_id"] == str(asset.id)
        assert data["permissions"] == "view"
        assert data["access_count"] == 1

    async def test_access_share_expired(
        self, client, db_session, make_asset, make_auth_headers
    ):
        headers, user_id = make_auth_headers()
        asset = make_asset(created_by=user_id)
        db_session.add(asset)
        await db_session.flush()

        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        create_resp = await client.post(
            "/api/shares/",
            headers=headers,
            json={"asset_id": str(asset.id), "expires_at": past},
        )
        token = create_resp.json()["token"]

        resp = await client.get(f"/api/shares/{token}/access")
        assert resp.status_code == 410

    async def test_access_share_wrong_password(
        self, client, db_session, make_asset, make_auth_headers
    ):
        headers, user_id = make_auth_headers()
        asset = make_asset(created_by=user_id)
        db_session.add(asset)
        await db_session.flush()

        create_resp = await client.post(
            "/api/shares/",
            headers=headers,
            json={"asset_id": str(asset.id), "password": "secret123"},
        )
        token = create_resp.json()["token"]

        # Access without password
        resp = await client.get(f"/api/shares/{token}/access")
        assert resp.status_code == 403

        # Access with wrong password
        resp = await client.get(
            f"/api/shares/{token}/access", params={"password": "wrong"}
        )
        assert resp.status_code == 403

        # Access with correct password
        resp = await client.get(
            f"/api/shares/{token}/access", params={"password": "secret123"}
        )
        assert resp.status_code == 200

    async def test_revoke_share(
        self, client, db_session, make_asset, make_auth_headers
    ):
        headers, user_id = make_auth_headers()
        asset = make_asset(created_by=user_id)
        db_session.add(asset)
        await db_session.flush()

        create_resp = await client.post(
            "/api/shares/",
            headers=headers,
            json={"asset_id": str(asset.id)},
        )
        share_id = create_resp.json()["id"]
        token = create_resp.json()["token"]

        # Revoke
        resp = await client.delete(
            f"/api/shares/{share_id}", headers=headers
        )
        assert resp.status_code == 204

        # Access should fail
        resp = await client.get(f"/api/shares/{token}/access")
        assert resp.status_code == 404

    async def test_share_increments_access_count(
        self, client, db_session, make_asset, make_auth_headers
    ):
        headers, user_id = make_auth_headers()
        asset = make_asset(created_by=user_id)
        db_session.add(asset)
        await db_session.flush()

        create_resp = await client.post(
            "/api/shares/",
            headers=headers,
            json={"asset_id": str(asset.id)},
        )
        token = create_resp.json()["token"]

        # Access 3 times
        for i in range(3):
            resp = await client.get(f"/api/shares/{token}/access")
            assert resp.status_code == 200
            assert resp.json()["access_count"] == i + 1
