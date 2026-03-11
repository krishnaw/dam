from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReviewSubmit(BaseModel):
    comment: str | None = None


class ReviewAction(BaseModel):
    action: Literal["approve", "reject"]
    comment: str | None = None


class CommentCreate(BaseModel):
    content: str
    parent_id: UUID | None = None
    annotation_data: dict | None = None


class CommentResponse(BaseModel):
    id: UUID
    content: str
    user_id: UUID
    parent_id: UUID | None = None
    annotation_data: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Workflow schemas ---


class WorkflowStepConfig(BaseModel):
    name: str
    step_type: str = "approval"
    reviewer_id: UUID | None = None
    due_date: datetime | None = None


class WorkflowStepResponse(BaseModel):
    id: UUID
    step_order: int
    step_type: str
    status: str
    reviewer_id: UUID | None = None
    comment: str | None = None
    due_date: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None
    asset_id: UUID
    template_id: UUID | None = None
    steps: list[WorkflowStepConfig] | None = None


class WorkflowResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    asset_id: UUID
    status: str
    created_by: UUID
    steps: list[WorkflowStepResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowTemplateCreate(BaseModel):
    name: str
    description: str | None = None
    steps_config: list[dict]


class WorkflowTemplateResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    steps_config: list[dict] | dict
    created_by: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(BaseModel):
    id: UUID
    notification_type: str
    message: str
    asset_id: UUID | None = None
    is_read: bool
    data: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
