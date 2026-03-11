"""Integration tests for workflow API endpoints (review + comments)."""

import uuid

import pytest


class TestReviewWorkflow:
    async def test_submit_for_review(
        self, client, auth_headers, db_session, make_asset
    ):
        asset = make_asset()
        db_session.add(asset)
        await db_session.flush()

        resp = await client.post(
            f"/api/assets/{asset.id}/review",
            headers=auth_headers,
            json={"comment": "Please review this asset"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["status"] == "submitted"

    async def test_approve_asset(
        self, client, auth_headers, db_session, make_asset
    ):
        asset = make_asset()
        db_session.add(asset)
        await db_session.flush()

        # Submit for review
        await client.post(
            f"/api/assets/{asset.id}/review",
            headers=auth_headers,
            json={"comment": "Review please"},
        )

        # Approve
        resp = await client.put(
            f"/api/assets/{asset.id}/review",
            headers=auth_headers,
            json={"action": "approve", "comment": "LGTM"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    async def test_reject_asset(
        self, client, auth_headers, db_session, make_asset
    ):
        asset = make_asset()
        db_session.add(asset)
        await db_session.flush()

        # Submit for review
        await client.post(
            f"/api/assets/{asset.id}/review",
            headers=auth_headers,
            json={},
        )

        # Reject
        resp = await client.put(
            f"/api/assets/{asset.id}/review",
            headers=auth_headers,
            json={"action": "reject", "comment": "Needs more work"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    async def test_review_nonexistent_asset(self, client, auth_headers):
        resp = await client.post(
            f"/api/assets/{uuid.uuid4()}/review",
            headers=auth_headers,
            json={},
        )
        assert resp.status_code == 404


class TestComments:
    async def test_add_comment(
        self, client, auth_headers, db_session, make_asset
    ):
        asset = make_asset()
        db_session.add(asset)
        await db_session.flush()

        resp = await client.post(
            f"/api/assets/{asset.id}/comments",
            headers=auth_headers,
            json={"content": "This looks great!"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["content"] == "This looks great!"
        assert data["parent_id"] is None

    async def test_threaded_comment(
        self, client, auth_headers, db_session, make_asset
    ):
        asset = make_asset()
        db_session.add(asset)
        await db_session.flush()

        # Add parent comment
        parent_resp = await client.post(
            f"/api/assets/{asset.id}/comments",
            headers=auth_headers,
            json={"content": "Parent comment"},
        )
        parent_id = parent_resp.json()["id"]

        # Reply to parent
        resp = await client.post(
            f"/api/assets/{asset.id}/comments",
            headers=auth_headers,
            json={"content": "Reply to parent", "parent_id": parent_id},
        )
        assert resp.status_code == 201
        assert resp.json()["parent_id"] == parent_id

    async def test_list_comments(
        self, client, auth_headers, db_session, make_asset
    ):
        asset = make_asset()
        db_session.add(asset)
        await db_session.flush()

        # Add multiple comments
        for text in ["First", "Second", "Third"]:
            await client.post(
                f"/api/assets/{asset.id}/comments",
                headers=auth_headers,
                json={"content": text},
            )

        resp = await client.get(
            f"/api/assets/{asset.id}/comments",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        contents = {c["content"] for c in data}
        assert "First" in contents
        assert "Second" in contents
        assert "Third" in contents

    async def test_comment_with_annotation(
        self, client, auth_headers, db_session, make_asset
    ):
        asset = make_asset()
        db_session.add(asset)
        await db_session.flush()

        resp = await client.post(
            f"/api/assets/{asset.id}/comments",
            headers=auth_headers,
            json={
                "content": "Fix this area",
                "annotation_data": {"x": 100, "y": 200, "w": 50, "h": 50},
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["annotation_data"] == {"x": 100, "y": 200, "w": 50, "h": 50}
