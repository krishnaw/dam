"""Unit tests for SQLAlchemy models."""

import uuid
from datetime import datetime, timezone

from app.models.asset import Asset, AssetStatus, AssetVersion, Rendition, RenditionType
from app.models.collection import Collection, CollectionAsset, CollectionType
from app.models.metadata import AssetMetadata, MetadataSource
from app.models.user import RefreshToken, User, UserRole
from app.models.workflow import Comment, ReviewStatus, WorkflowStep


class TestAssetModel:
    def test_asset_creation(self, make_asset):
        asset = make_asset()
        assert asset.id is not None
        assert asset.filename.endswith(".jpg")
        assert asset.original_filename == "test-image.jpg"
        assert asset.content_type == "image/jpeg"
        assert asset.file_size == 1024000
        assert asset.width == 1920
        assert asset.height == 1080
        assert asset.storage_path.startswith("assets/")
        assert asset.status == AssetStatus.active

    def test_asset_status_enum(self):
        assert AssetStatus.draft.value == "draft"
        assert AssetStatus.processing.value == "processing"
        assert AssetStatus.active.value == "active"
        assert AssetStatus.archived.value == "archived"
        assert len(AssetStatus) == 4

    def test_asset_version_creation(self):
        asset_id = uuid.uuid4()
        version = AssetVersion(
            id=uuid.uuid4(),
            asset_id=asset_id,
            version_number=1,
            storage_path="versions/test.jpg",
            file_size=500000,
            change_notes="Initial upload",
        )
        assert version.asset_id == asset_id
        assert version.version_number == 1
        assert version.storage_path == "versions/test.jpg"
        assert version.file_size == 500000
        assert version.change_notes == "Initial upload"

    def test_rendition_creation(self):
        asset_id = uuid.uuid4()
        rendition = Rendition(
            id=uuid.uuid4(),
            asset_id=asset_id,
            rendition_type=RenditionType.thumbnail,
            storage_path="thumbnails/test.jpg",
            width=300,
            height=300,
            file_format="jpeg",
            file_size=15000,
        )
        assert rendition.asset_id == asset_id
        assert rendition.rendition_type == RenditionType.thumbnail
        assert rendition.width == 300
        assert rendition.height == 300
        assert rendition.file_format == "jpeg"

    def test_rendition_type_enum(self):
        assert RenditionType.original.value == "original"
        assert RenditionType.thumbnail.value == "thumbnail"
        assert RenditionType.preview.value == "preview"
        assert RenditionType.web.value == "web"
        assert len(RenditionType) == 4


class TestUserModel:
    def test_user_creation(self, make_user):
        user = make_user(email="alice@example.com", role="admin", full_name="Alice Admin")
        assert user.email == "alice@example.com"
        assert user.role == "admin"
        assert user.full_name == "Alice Admin"
        assert user.is_active is True
        assert user.hashed_password is not None
        assert user.hashed_password != "testpass123"  # should be hashed

    def test_user_role_enum(self):
        assert UserRole.admin.value == "admin"
        assert UserRole.manager.value == "manager"
        assert UserRole.editor.value == "editor"
        assert UserRole.reviewer.value == "reviewer"
        assert UserRole.viewer.value == "viewer"
        assert len(UserRole) == 5


class TestCollectionModel:
    def test_collection_creation(self):
        coll = Collection(
            id=uuid.uuid4(),
            name="Marketing Assets",
            description="All marketing materials",
            collection_type=CollectionType.collection,
        )
        assert coll.name == "Marketing Assets"
        assert coll.description == "All marketing materials"
        assert coll.collection_type == CollectionType.collection
        assert coll.parent_id is None

    def test_collection_type_enum(self):
        assert CollectionType.folder.value == "folder"
        assert CollectionType.collection.value == "collection"
        assert len(CollectionType) == 2

    def test_collection_as_folder(self):
        folder = Collection(
            id=uuid.uuid4(),
            name="2024 Campaign",
            collection_type=CollectionType.folder,
        )
        assert folder.collection_type == CollectionType.folder

    def test_collection_asset_association(self):
        collection_id = uuid.uuid4()
        asset_id = uuid.uuid4()
        ca = CollectionAsset(
            id=uuid.uuid4(),
            collection_id=collection_id,
            asset_id=asset_id,
            position=0,
        )
        assert ca.collection_id == collection_id
        assert ca.asset_id == asset_id
        assert ca.position == 0


class TestWorkflowModel:
    def test_comment_creation(self):
        asset_id = uuid.uuid4()
        user_id = uuid.uuid4()
        comment = Comment(
            id=uuid.uuid4(),
            asset_id=asset_id,
            user_id=user_id,
            content="Looks great!",
        )
        assert comment.asset_id == asset_id
        assert comment.user_id == user_id
        assert comment.content == "Looks great!"
        assert comment.parent_id is None
        assert comment.annotation_data is None

    def test_comment_with_parent_for_threading(self):
        parent_id = uuid.uuid4()
        comment = Comment(
            id=uuid.uuid4(),
            asset_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            content="I agree!",
            parent_id=parent_id,
        )
        assert comment.parent_id == parent_id

    def test_comment_with_annotation_data(self):
        comment = Comment(
            id=uuid.uuid4(),
            asset_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            content="Fix this area",
            annotation_data={"x": 100, "y": 200, "width": 50, "height": 50},
        )
        assert comment.annotation_data == {"x": 100, "y": 200, "width": 50, "height": 50}

    def test_workflow_step_creation(self):
        asset_id = uuid.uuid4()
        step = WorkflowStep(
            id=uuid.uuid4(),
            asset_id=asset_id,
            status=ReviewStatus.submitted,
            comment="Please review",
        )
        assert step.asset_id == asset_id
        assert step.status == ReviewStatus.submitted
        assert step.comment == "Please review"
        assert step.reviewer_id is None

    def test_review_status_enum(self):
        assert ReviewStatus.submitted.value == "submitted"
        assert ReviewStatus.in_review.value == "in_review"
        assert ReviewStatus.approved.value == "approved"
        assert ReviewStatus.rejected.value == "rejected"
        assert len(ReviewStatus) == 4


class TestMetadataModel:
    def test_metadata_creation(self):
        asset_id = uuid.uuid4()
        meta = AssetMetadata(
            id=uuid.uuid4(),
            asset_id=asset_id,
            key="camera_model",
            value="Canon EOS R5",
            source=MetadataSource.exif,
        )
        assert meta.asset_id == asset_id
        assert meta.key == "camera_model"
        assert meta.value == "Canon EOS R5"
        assert meta.source == MetadataSource.exif

    def test_metadata_source_enum(self):
        assert MetadataSource.manual.value == "manual"
        assert MetadataSource.auto.value == "auto"
        assert MetadataSource.exif.value == "exif"
        assert len(MetadataSource) == 3
