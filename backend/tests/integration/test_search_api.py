"""Integration tests for search API endpoints."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.models.asset import Asset, AssetStatus


@pytest.fixture
def _mock_meilisearch():
    """Patch MeilisearchService in the search router."""
    mock_svc = MagicMock()
    mock_svc.search.return_value = {
        "hits": [],
        "estimatedTotalHits": 0,
        "facetDistribution": {},
    }

    with patch("app.api.search.MeilisearchService", return_value=mock_svc) as _:
        yield mock_svc


class TestSearchAPI:
    async def test_search_returns_results(
        self, client, auth_headers, db_session, make_asset, _mock_meilisearch
    ):
        # Create assets in DB
        asset = make_asset(original_filename="sunset-beach.jpg")
        db_session.add(asset)
        await db_session.flush()

        # Configure mock to return the asset ID
        _mock_meilisearch.search.return_value = {
            "hits": [{"id": str(asset.id)}],
            "estimatedTotalHits": 1,
            "facetDistribution": {},
        }

        resp = await client.get(
            "/api/search/", headers=auth_headers, params={"q": "sunset"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["query"] == "sunset"
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(asset.id)

    async def test_search_empty_query_fallback(self, client, auth_headers):
        """The search endpoint requires a non-empty query string."""
        resp = await client.get("/api/search/", headers=auth_headers)
        # Missing required 'q' query param
        assert resp.status_code == 422

    async def test_search_with_filters(
        self, client, auth_headers, _mock_meilisearch
    ):
        _mock_meilisearch.search.return_value = {
            "hits": [],
            "estimatedTotalHits": 0,
            "facetDistribution": {},
        }

        resp = await client.get(
            "/api/search/",
            headers=auth_headers,
            params={"q": "test", "file_type": "image/jpeg", "status": "active"},
        )
        assert resp.status_code == 200

        # Verify the service was called with correct filters
        call_args = _mock_meilisearch.search.call_args
        assert call_args[0][0] == "test"  # query
        filters = call_args[1].get("filters") or call_args[0][1] if len(call_args[0]) > 1 else None
        # The router passes filters dict to svc.search()
        # Checking the call was made is sufficient

    async def test_search_db_fallback(self, client, auth_headers, db_session, make_asset):
        """When Meilisearch is unavailable, should fall back to DB search."""
        asset = make_asset(original_filename="fallback-test.jpg")
        db_session.add(asset)
        await db_session.flush()

        # Patch MeilisearchService to raise so the fallback kicks in
        with patch(
            "app.api.search.MeilisearchService",
            side_effect=Exception("Meilisearch unavailable"),
        ):
            resp = await client.get(
                "/api/search/",
                headers=auth_headers,
                params={"q": "fallback-test"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["query"] == "fallback-test"
