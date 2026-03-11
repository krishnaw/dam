import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReviewStatus(str, enum.Enum):
    submitted = "submitted"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"


class Workflow(Base):
    __tablename__ = "workflows"

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    steps: Mapped[list["WorkflowStep"]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowStep.step_order",
    )


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE")
    )
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"), nullable=True
    )
    step_order: Mapped[int] = mapped_column(Integer, default=0)
    step_type: Mapped[str] = mapped_column(String(50), default="approval")
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus), default=ReviewStatus.submitted
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    workflow: Mapped["Workflow | None"] = relationship(back_populates="steps")


class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps_config: Mapped[dict] = mapped_column(JSON)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))


class Comment(Base):
    __tablename__ = "comments"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("comments.id", ondelete="SET NULL"), nullable=True
    )
    annotation_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="comments")
    replies: Mapped[list["Comment"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    parent: Mapped["Comment | None"] = relationship(
        back_populates="replies", remote_side="Comment.id"
    )


class ShareLink(Base):
    __tablename__ = "share_links"

    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"), nullable=True
    )
    collection_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_hash: Mapped[str | None] = mapped_column(String(200), nullable=True)
    permissions: Mapped[str] = mapped_column(String(50), default="view")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    access_count: Mapped[int] = mapped_column(Integer, default=0)


class Notification(Base):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    notification_type: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL"), nullable=True
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
