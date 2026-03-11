from fastapi import APIRouter

router = APIRouter(prefix="/api/metadata", tags=["metadata"])


@router.get("/")
async def list_metadata_schemas():
    """Placeholder for metadata schema CRUD - MVP."""
    return {"schemas": []}
