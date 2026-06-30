from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import WorkspaceRole


class WorkspaceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime


class WorkspaceMembershipSummary(BaseModel):
    workspace_id: UUID
    role: WorkspaceRole
    workspace: WorkspaceSummary


class ActiveWorkspaceResponse(BaseModel):
    workspace_id: UUID
    role: WorkspaceRole
    workspace: WorkspaceSummary
