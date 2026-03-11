import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    Asset,
    Comment,
    Notification,
    ReviewStatus,
    User,
    Workflow,
    WorkflowStep,
    WorkflowTemplate,
)
from app.schemas.workflow import (
    CommentCreate,
    CommentResponse,
    NotificationResponse,
    ReviewAction,
    ReviewSubmit,
    WorkflowCreate,
    WorkflowResponse,
    WorkflowTemplateCreate,
    WorkflowTemplateResponse,
)
from app.services.auth import get_current_user, require_reviewer
from app.services.notifications import NotificationService

router = APIRouter(tags=["workflows"])

# ---------------------------------------------------------------------------
# Legacy per-asset review endpoints (kept for backward compatibility)
# ---------------------------------------------------------------------------

asset_router = APIRouter(prefix="/api/assets/{asset_id}", tags=["workflows"])


@asset_router.post("/review", status_code=status.HTTP_201_CREATED)
async def submit_for_review(
    asset_id: UUID,
    body: ReviewSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Asset not found")

    step = WorkflowStep(
        asset_id=asset_id,
        status=ReviewStatus.submitted,
        comment=body.comment,
    )
    db.add(step)
    await db.flush()
    await db.refresh(step)
    return {"id": str(step.id), "status": step.status.value}


@asset_router.put("/review")
async def review_asset(
    asset_id: UUID,
    body: ReviewAction,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_reviewer),
):
    result = await db.execute(
        select(WorkflowStep)
        .where(WorkflowStep.asset_id == asset_id)
        .order_by(WorkflowStep.created_at.desc())
    )
    step = result.scalars().first()
    if not step:
        raise HTTPException(status_code=404, detail="No review found for this asset")

    if body.action == "approve":
        step.status = ReviewStatus.approved
    else:
        step.status = ReviewStatus.rejected

    step.reviewer_id = UUID(current_user["sub"])
    step.comment = body.comment or step.comment
    return {"id": str(step.id), "status": step.status.value}


@asset_router.get("/comments", response_model=list[CommentResponse])
async def list_comments(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Comment)
        .where(Comment.asset_id == asset_id)
        .order_by(Comment.created_at)
    )
    return result.scalars().all()


@asset_router.post(
    "/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    asset_id: UUID,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Asset not found")

    comment = Comment(
        asset_id=asset_id,
        user_id=UUID(current_user["sub"]),
        content=body.content,
        parent_id=body.parent_id,
        annotation_data=body.annotation_data,
    )
    db.add(comment)
    await db.flush()
    await db.refresh(comment)

    # Parse @mentions and create notifications
    mentions = re.findall(r"@(\w+)", body.content)
    if mentions:
        svc = NotificationService(db)
        # Look up mentioned users by email prefix or full_name
        for mention in mentions:
            user_result = await db.execute(
                select(User).where(User.full_name.ilike(f"%{mention}%"))
            )
            mentioned_user = user_result.scalars().first()
            if mentioned_user:
                await svc.notify_comment(
                    asset_id=asset_id,
                    mentioned_user_ids=[mentioned_user.id],
                    commenter_name=current_user.get("sub", "Someone"),
                )

    return comment


# ---------------------------------------------------------------------------
# Multi-step workflow endpoints
# ---------------------------------------------------------------------------

workflow_router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@workflow_router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    body: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Verify asset exists
    result = await db.execute(select(Asset).where(Asset.id == body.asset_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Asset not found")

    steps_config = None

    # If template_id provided, load template steps
    if body.template_id:
        tmpl_result = await db.execute(
            select(WorkflowTemplate).where(WorkflowTemplate.id == body.template_id)
        )
        template = tmpl_result.scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        steps_config = template.steps_config

    workflow = Workflow(
        name=body.name,
        description=body.description,
        asset_id=body.asset_id,
        status="active",
        created_by=UUID(current_user["sub"]),
    )
    db.add(workflow)
    await db.flush()

    # Create steps from template or body
    step_defs = body.steps or []
    if steps_config and not step_defs:
        # Use template steps_config
        for i, sc in enumerate(steps_config):
            step = WorkflowStep(
                asset_id=body.asset_id,
                workflow_id=workflow.id,
                step_order=i,
                step_type=sc.get("step_type", "approval"),
                status=ReviewStatus.submitted,
                comment=sc.get("name", ""),
            )
            db.add(step)
    else:
        for i, step_cfg in enumerate(step_defs):
            step = WorkflowStep(
                asset_id=body.asset_id,
                workflow_id=workflow.id,
                step_order=i,
                step_type=step_cfg.step_type,
                status=ReviewStatus.submitted,
                reviewer_id=step_cfg.reviewer_id,
                due_date=step_cfg.due_date,
                comment=step_cfg.name,
            )
            db.add(step)

    await db.flush()

    # Reload with steps
    result = await db.execute(
        select(Workflow)
        .options(selectinload(Workflow.steps))
        .where(Workflow.id == workflow.id)
    )
    workflow = result.scalar_one()
    return workflow


@workflow_router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Workflow)
        .options(selectinload(Workflow.steps))
        .where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@workflow_router.put("/{workflow_id}/steps/{step_id}")
async def update_workflow_step(
    workflow_id: UUID,
    step_id: UUID,
    body: ReviewAction,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_reviewer),
):
    result = await db.execute(
        select(WorkflowStep).where(
            WorkflowStep.id == step_id,
            WorkflowStep.workflow_id == workflow_id,
        )
    )
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    if body.action == "approve":
        step.status = ReviewStatus.approved
    else:
        step.status = ReviewStatus.rejected

    step.reviewer_id = UUID(current_user["sub"])
    if body.comment:
        step.comment = body.comment

    await db.flush()

    # Create notification for workflow owner
    wf_result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = wf_result.scalar_one_or_none()
    if workflow:
        svc = NotificationService(db)
        action_text = "approved" if body.action == "approve" else "rejected"
        await svc.create(
            user_id=workflow.created_by,
            notification_type="review_submitted",
            message=f"Step {action_text} by reviewer",
            asset_id=workflow.asset_id,
        )

        # Check if all steps are approved -> complete workflow
        steps_result = await db.execute(
            select(WorkflowStep).where(WorkflowStep.workflow_id == workflow_id)
        )
        all_steps = steps_result.scalars().all()
        if all(s.status == ReviewStatus.approved for s in all_steps):
            workflow.status = "completed"
        elif any(s.status == ReviewStatus.rejected for s in all_steps):
            workflow.status = "active"  # remains active, needs rework

    return {"id": str(step.id), "status": step.status.value}


# ---------------------------------------------------------------------------
# Workflow templates
# ---------------------------------------------------------------------------


@workflow_router.get("/templates/", response_model=list[WorkflowTemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(WorkflowTemplate).order_by(WorkflowTemplate.created_at.desc())
    )
    return result.scalars().all()


@workflow_router.post(
    "/templates/",
    response_model=WorkflowTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    body: WorkflowTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    template = WorkflowTemplate(
        name=body.name,
        description=body.description,
        steps_config=body.steps_config,
        created_by=UUID(current_user["sub"]),
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return template


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

notification_router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@notification_router.get("/", response_model=list[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    svc = NotificationService(db)
    return await svc.get_user_notifications(
        user_id=UUID(current_user["sub"]),
        unread_only=unread_only,
    )


@notification_router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    svc = NotificationService(db)
    success = await svc.mark_read(notification_id, UUID(current_user["sub"]))
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "ok"}


@notification_router.put("/read-all")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    svc = NotificationService(db)
    count = await svc.mark_all_read(UUID(current_user["sub"]))
    return {"marked_read": count}
