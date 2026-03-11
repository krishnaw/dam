"""Unit tests for Meilisearch service."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.search import MeilisearchService


@pytest.fixture
def search_svc():
    """Create MeilisearchService with a mocked client."""
    with patch("app.services.search.meilisearch.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        svc = MeilisearchService(url="http://test:7700", key="test-key")
        svc._mock_client = mock_client
        yield svc


class TestMeilisearchService:
    def test_index_asset_calls_add_documents(self, search_svc):
        mock_index = MagicMock()
        search_svc._mock_client.index.return_value = mock_index

        doc = {
            "id": "abc-123",
            "filename": "test.jpg",
            "original_filename": "photo.jpg",
            "content_type": "image/jpeg",
            "file_size": 1024,
            "description": "A test photo",
            "status": "active",
        }
        search_svc.index_asset(doc)

        search_svc._mock_client.index.assert_called_with("assets")
        mock_index.add_documents.assert_called_once_with([doc])

    def test_search_with_query(self, search_svc):
        mock_index = MagicMock()
        mock_index.search.return_value = {
            "hits": [{"id": "1"}],
            "estimatedTotalHits": 1,
        }
        search_svc._mock_client.index.return_value = mock_index

        result = search_svc.search("landscape")
        mock_index.search.assert_called_once()
        call_args = mock_index.search.call_args
        assert call_args[0][0] == "landscape"
        assert result["estimatedTotalHits"] == 1

    def test_search_with_filters(self, search_svc):
        mock_index = MagicMock()
        mock_index.search.return_value = {"hits": [], "estimatedTotalHits": 0}
        search_svc._mock_client.index.return_value = mock_index

        search_svc.search(
            "test",
            filters={"content_type": "image/jpeg", "status": "active"},
        )
        call_args = mock_index.search.call_args
        search_params = call_args[0][1]
        assert "filter" in search_params
        assert 'content_type = "image/jpeg"' in search_params["filter"]
        assert 'status = "active"' in search_params["filter"]

    def test_search_with_size_filters(self, search_svc):
        mock_index = MagicMock()
        mock_index.search.return_value = {"hits": [], "estimatedTotalHits": 0}
        search_svc._mock_client.index.return_value = mock_index

        search_svc.search(
            "test",
            filters={"file_size_min": 1000, "file_size_max": 5000000},
        )
        call_args = mock_index.search.call_args
        search_params = call_args[0][1]
        assert "file_size >= 1000" in search_params["filter"]
        assert "file_size <= 5000000" in search_params["filter"]

    def test_search_pagination(self, search_svc):
        mock_index = MagicMock()
        mock_index.search.return_value = {"hits": [], "estimatedTotalHits": 0}
        search_svc._mock_client.index.return_value = mock_index

        search_svc.search("test", page=3, page_size=20)
        call_args = mock_index.search.call_args
        search_params = call_args[0][1]
        assert search_params["offset"] == 40  # (3-1) * 20
        assert search_params["limit"] == 20

    def test_delete_document_calls_delete(self, search_svc):
        mock_index = MagicMock()
        search_svc._mock_client.index.return_value = mock_index

        search_svc.delete_document("abc-123")
        search_svc._mock_client.index.assert_called_with("assets")
        mock_index.delete_document.assert_called_once_with("abc-123")

    def test_ensure_index_configures_filterable(self, search_svc):
        mock_index = MagicMock()
        search_svc._mock_client.index.return_value = mock_index

        search_svc.ensure_index()

        search_svc._mock_client.create_index.assert_called_once_with(
            "assets", {"primaryKey": "id"}
        )
        mock_index.update_filterable_attributes.assert_called_once_with(
            ["content_type", "status", "file_size", "created_at"]
        )
        mock_index.update_sortable_attributes.assert_called_once_with(
            ["created_at", "file_size", "original_filename"]
        )
