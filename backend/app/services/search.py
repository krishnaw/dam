import meilisearch

from app.config import settings


class MeilisearchService:
    def __init__(
        self,
        url: str | None = None,
        key: str | None = None,
    ) -> None:
        self.client = meilisearch.Client(
            url or settings.MEILISEARCH_URL,
            key or settings.MEILISEARCH_KEY,
        )

    def ensure_index(self, index_name: str = "assets") -> None:
        """Create index if not exists and configure filterable/sortable attributes."""
        try:
            self.client.create_index(index_name, {"primaryKey": "id"})
        except meilisearch.errors.MeilisearchApiError:
            pass  # Index already exists

        index = self.client.index(index_name)
        index.update_filterable_attributes(
            ["content_type", "status", "file_size", "created_at"]
        )
        index.update_sortable_attributes(["created_at", "file_size", "original_filename"])

    def index_asset(self, asset: dict, index_name: str = "assets") -> None:
        """Add or update a document in the index."""
        index = self.client.index(index_name)
        index.add_documents([asset])

    def search(
        self,
        query: str,
        filters: dict | None = None,
        page: int = 1,
        page_size: int = 50,
        index_name: str = "assets",
    ) -> dict:
        """Search with filters and pagination."""
        index = self.client.index(index_name)

        search_params: dict = {
            "offset": (page - 1) * page_size,
            "limit": page_size,
        }

        if filters:
            filter_parts = []
            for key, value in filters.items():
                if key == "file_size_min":
                    filter_parts.append(f"file_size >= {value}")
                elif key == "file_size_max":
                    filter_parts.append(f"file_size <= {value}")
                else:
                    filter_parts.append(f'{key} = "{value}"')
            if filter_parts:
                search_params["filter"] = " AND ".join(filter_parts)

        return index.search(query, search_params)

    def delete_document(self, asset_id: str, index_name: str = "assets") -> None:
        """Remove document from index."""
        index = self.client.index(index_name)
        index.delete_document(asset_id)
