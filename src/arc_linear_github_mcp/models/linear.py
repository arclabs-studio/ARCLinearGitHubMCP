"""Pydantic models for Linear API entities."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Priority(int, Enum):
    """Linear issue priority levels."""

    NO_PRIORITY = 0
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class IssueState(BaseModel):
    """Linear issue state."""

    id: str
    name: str
    type: str | None = None
    color: str | None = None


class User(BaseModel):
    """Linear user model."""

    id: str
    name: str
    email: str | None = None
    display_name: str | None = Field(None, alias="displayName")


class Label(BaseModel):
    """Linear label model."""

    id: str
    name: str
    color: str | None = None


class Project(BaseModel):
    """Linear project model."""

    id: str
    name: str
    key: str | None = None
    description: str | None = None


class Team(BaseModel):
    """Linear team model."""

    id: str
    name: str
    key: str


class Issue(BaseModel):
    """Linear issue model."""

    id: str
    identifier: str
    title: str
    description: str | None = None
    priority: int = Priority.NORMAL
    priority_label: str | None = Field(None, alias="priorityLabel")
    state: IssueState | None = None
    assignee: User | None = None
    creator: User | None = None
    labels: list[Label] = Field(default_factory=list)
    project: Project | None = None
    team: Team | None = None
    url: str | None = None
    created_at: datetime | None = Field(None, alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt")

    def to_dict(self) -> dict:
        """Convert to dictionary for MCP response."""
        return {
            "id": self.id,
            "identifier": self.identifier,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "priority_label": self.priority_label,
            "state": self.state.name if self.state else None,
            "assignee": self.assignee.name if self.assignee else None,
            "labels": [label.name for label in self.labels],
            "url": self.url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CreateIssueRequest(BaseModel):
    """Request model for creating a Linear issue."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=10000)
    team_id: str = Field(..., description="Linear team ID")
    project_id: str | None = Field(None, description="Linear project ID")
    priority: int = Field(
        default=Priority.NORMAL,
        ge=0,
        le=4,
        description="Priority: 0=None, 1=Urgent, 2=High, 3=Normal, 4=Low",
    )
    label_ids: list[str] = Field(default_factory=list)
    assignee_id: str | None = None
    state_id: str | None = None


class UpdateIssueRequest(BaseModel):
    """Request model for updating a Linear issue."""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = Field(None, max_length=10000)
    priority: int | None = Field(None, ge=0, le=4)
    state_id: str | None = None
    assignee_id: str | None = None
    label_ids: list[str] | None = None


class IssueConnection(BaseModel):
    """Linear issue connection for pagination."""

    nodes: list[Issue] = Field(default_factory=list)
    page_info: dict | None = Field(None, alias="pageInfo")


class TeamConnection(BaseModel):
    """Linear team connection for pagination."""

    nodes: list[Team] = Field(default_factory=list)


class WorkflowState(BaseModel):
    """Linear workflow state model."""

    id: str
    name: str
    type: str
    color: str | None = None
    team: Team | None = None
