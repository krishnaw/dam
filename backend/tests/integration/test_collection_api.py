"""Integration tests for collection API endpoints."""

import uuid

import pytest


class TestCreateCollection:
    async def test_create_collection(self, client, auth_headers):
        resp = await client.post(
            "/api/collections/",
            headers=auth_headers,
            json={"name": "Marketing", "description": "Marketing assets"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Marketing"
        assert data["description"] == "Marketing assets"
        assert data["collection_type"] == "collection"
        assert data["parent_id"] is None

    async def test_create_folder(self, client, auth_headers):
        resp = await client.post(
            "/api/collections/",
            headers=auth_headers,
            json={
                "name": "2024 Campaign",
                "collection_type": "folder",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["collection_type"] == "folder"


class TestListCollections:
    async def test_list_collections(self, client, auth_headers):
        # Create a few collections
        for name in ["Alpha", "Beta", "Gamma"]:
            await client.post(
                "/api/collections/",
                headers=auth_headers,
                json={"name": name},
            )

        resp = await client.get("/api/collections/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        names = {c["name"] for c in data}
        assert "Alpha" in names
        assert "Beta" in names
        assert "Gamma" in names


class TestGetCollection:
    async def test_get_collection(self, client, auth_headers):
        create_resp = await client.post(
            "/api/collections/",
            headers=auth_headers,
            json={"name": "Detail Test"},
        )
        cid = create_resp.json()["id"]

        resp = await client.get(f"/api/collections/{cid}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == cid
        assert data["name"] == "Detail Test"
        assert "assets" in data  # CollectionWithAssetsResponse

    async def test_get_collection_not_found(self, client, auth_headers):
        resp = await client.get(
            f"/api/collections/{uuid.uuid4()}", headers=auth_headers
        )
        assert resp.status_code == 404


class TestUpdateCollection:
    async def test_update_collection(self, client, auth_headers):
        create_resp = await client.post(
            "/api/collections/",
            headers=auth_headers,
            json={"name": "Old Name"},
        )
        cid = create_resp.json()["id"]

        resp = await client.put(
            f"/api/collections/{cid}",
            headers=auth_headers,
            json={"name": "New Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"


class TestDeleteCollection:
    async def test_delete_collection(self, client, auth_headers):
        create_resp = await client.post(
            "/api/collections/",
            headers=auth_headers,
            json={"name": "To Delete"},
        )
        cid = create_resp.json()["id"]

        resp = await client.delete(f"/api/collections/{cid}", headers=auth_headers)
        assert resp.status_code == 204

        # Verify it's gone
        get_resp = await client.get(f"/api/collections/{cid}", headers=auth_headers)
        assert get_resp.status_code == 404


class TestCollectionAssets:
    async def test_add_asset_to_collection(
        self, client, auth_headers, db_session, make_asset
    ):
        # Create an asset
        asset = make_asset()
        db_session.add(asset)
        await db_session.flush()

        # Create a collection
        create_resp = await client.post(
            "/api/collections/",
            headers=auth_headers,
            json={"name": "With Assets"},
        )
        cid = create_resp.json()["id"]

        # Add asset to collection
        resp = await client.post(
            f"/api/collections/{cid}/assets",
            headers=auth_headers,
            json={"asset_id": str(asset.id)},
        )
        assert resp.status_code == 201

    async def test_remove_asset_from_collection(
        self, client, auth_headers, db_session, make_asset
    ):
        asset = make_asset()
        db_session.add(asset)
        await db_session.flush()

        create_resp = await client.post(
            "/api/collections/",
            headers=auth_headers,
            json={"name": "Remove Test"},
        )
        cid = create_resp.json()["id"]

        # Add then remove
        await client.post(
            f"/api/collections/{cid}/assets",
            headers=auth_headers,
            json={"asset_id": str(asset.id)},
        )

        resp = await client.delete(
            f"/api/collections/{cid}/assets/{asset.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204
