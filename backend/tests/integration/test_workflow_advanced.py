"""Integration tests for advanced workflow, template, and notification endpoints."""

import uuid

import pytest


class TestMultiStepWorkflows:
    async def test_create_multi_step_workflow(
        self, client, db_session, make_asset, make_auth_headers
    ):
        headers, user_id = make_auth_headers()
        asset = make_asset(created_by=user_id)
        db_session.add(asset)
        await db_session.flush()

        resp = await client.post(
            "/api/workflows/",
            headers=headers,
            json={
                "name": "Review Pipeline",
                "asset_id": str(asset.id),
                "steps": [
                    {"name": "Design Review", "step_type": "review"},
                    {"name": "Legal Approval", "step_type": "approval"},
                    {"name": "Final Sign-off", "step_type": "sign_off"},
                ],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Review Pipeline"
        assert data["status"] == "active"
        assert len(data["steps"]) == 3
        assert data["steps"][0]["step_type"] == "review"
        assert data["steps"][0]["step_order"] == 0
        assert data["steps"][1]["step_order"] == 1
        assert data["steps"][2]["step_order"] == 2

    async def test_approve_step_advances_workflow(
        self, client, db_session, make_asset, make_auth_headers
    ):
        headers, user_id = make_auth_headers()
        asset = make_asset(created_by=user_id)
        db_session.add(asset)
        await db_session.flush()

        # Create workflow with 2 steps
        create_resp = await client.post(
            "/api/workflows/",
            headers=headers,
            json={
                "name": "Two Step",
                "asset_id": str(asset.id),
                "steps": [
                    {"name": "Step 1", "step_type": "approval"},
                    {"name": "Step 2", "step_type": "approval"},
                ],
            },
        )
        wf = create_resp.json()
        wf_id = wf["id"]
        step1_id = wf["steps"][0]["id"]
        step2_id = wf["steps"][1]["id"]

        # Approve step 1
        resp = await client.put(
            f"/api/workflows/{wf_id}/steps/{step1_id}",
            headers=headers,
            json={"action": "approve", "comment": "Looks good"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

        # Approve step 2 -> workflow should complete
        resp = await client.put(
            f"/api/workflows/{wf_id}/steps/{step2_id}",
            headers=headers,
            json={"action": "approve"},
        )
        assert resp.status_code == 200

        # Verify workflow is completed
        wf_resp = await client.get(
            f"/api/workflows/{wf_id}", headers=headers
        )
        assert wf_resp.json()["status"] == "completed"

    async def test_reject_step(
        self, client, db_session, make_asset, make_auth_headers
    ):
        headers, user_id = make_auth_headers()
        asset = make_asset(created_by=user_id)
        db_session.add(asset)
        await db_session.flush()

        create_resp = await client.post(
            "/api/workflows/",
            headers=headers,
            json={
                "name": "Reject Test",
                "asset_id": str(asset.id),
                "steps": [{"name": "Review", "step_type": "approval"}],
            },
        )
        wf = create_resp.json()
        step_id = wf["steps"][0]["id"]

        resp = await client.put(
            f"/api/workflows/{wf['id']}/steps/{step_id}",
            headers=headers,
            json={"action": "reject", "comment": "Needs rework"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    async def test_create_workflow_from_template(
        self, client, db_session, make_asset, make_auth_headers
    ):
        headers, user_id = make_auth_headers()
        asset = make_asset(created_by=user_id)
        db_session.add(asset)
        await db_session.flush()

        # Create template
        tmpl_resp = await client.post(
            "/api/workflows/templates/",
            headers=headers,
            json={
                "name": "Standard Review",
                "description": "Default review process",
                "steps_config": [
                    {"name": "Initial Review", "step_type": "review"},
                    {"name": "Manager Approval", "step_type": "approval"},
                ],
            },
        )
        assert tmpl_resp.status_code == 201
        template_id = tmpl_resp.json()["id"]

        # Create workflow from template
        wf_resp = await client.post(
            "/api/workflows/",
            headers=headers,
            json={
                "name": "From Template",
                "asset_id": str(asset.id),
                "template_id": template_id,
            },
        )
        assert wf_resp.status_code == 201
        data = wf_resp.json()
        assert len(data["steps"]) == 2
        assert data["steps"][0]["step_type"] == "review"
        assert data["steps"][1]["step_type"] == "approval"


class TestNotifications:
    async def test_notifications_created_on_review(
        self, client, db_session, make_asset, make_auth_headers
    ):
        headers, user_id = make_auth_headers()
        asset = make_asset(created_by=user_id)
        db_session.add(asset)
        await db_session.flush()

        # Create workflow and approve a step (creates notification for workflow owner)
        create_resp = await client.post(
            "/api/workflows/",
            headers=headers,
            json={
                "name": "Notify Test",
                "asset_id": str(asset.id),
                "steps": [{"name": "Review", "step_type": "approval"}],
            },
        )
        wf = create_resp.json()
        step_id = wf["steps"][0]["id"]

        await client.put(
            f"/api/workflows/{wf['id']}/steps/{step_id}",
            headers=headers,
            json={"action": "approve"},
        )

        # Check notifications
        resp = await client.get("/api/notifications/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert any(n["notification_type"] == "review_submitted" for n in data)

    async def test_get_notifications(
        self, client, db_session, make_asset, make_auth_headers
    ):
        headers, user_id = make_auth_headers()
        asset = make_asset(created_by=user_id)
        db_session.add(asset)
        await db_session.flush()

        # Create a notification via a workflow step approval
        create_resp = await client.post(
            "/api/workflows/",
            headers=headers,
            json={
                "name": "Get Notif Test",
                "asset_id": str(asset.id),
                "steps": [{"name": "Step", "step_type": "approval"}],
            },
        )
        wf = create_resp.json()
        step_id = wf["steps"][0]["id"]
        await client.put(
            f"/api/workflows/{wf['id']}/steps/{step_id}",
            headers=headers,
            json={"action": "approve"},
        )

        resp = await client.get("/api/notifications/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        notif = data[0]
        assert "id" in notif
        assert "notification_type" in notif
        assert "message" in notif
        assert notif["is_read"] is False

    async def test_mark_notification_read(
        self, client, db_session, make_asset, make_auth_headers
    ):
        headers, user_id = make_auth_headers()
        asset = make_asset(created_by=user_id)
        db_session.add(asset)
        await db_session.flush()

        # Create notification via workflow
        create_resp = await client.post(
            "/api/workflows/",
            headers=headers,
            json={
                "name": "Mark Read Test",
                "asset_id": str(asset.id),
                "steps": [{"name": "Step", "step_type": "approval"}],
            },
        )
        wf = create_resp.json()
        step_id = wf["steps"][0]["id"]
        await client.put(
            f"/api/workflows/{wf['id']}/steps/{step_id}",
            headers=headers,
            json={"action": "approve"},
        )

        # Get notifications
        notifs_resp = await client.get("/api/notifications/", headers=headers)
        notif_id = notifs_resp.json()[0]["id"]

        # Mark as read
        resp = await client.put(
            f"/api/notifications/{notif_id}/read", headers=headers
        )
        assert resp.status_code == 200

        # Verify it's read
        notifs_resp = await client.get(
            "/api/notifications/", headers=headers, params={"unread_only": True}
        )
        notif_ids = [n["id"] for n in notifs_resp.json()]
        assert notif_id not in notif_ids
