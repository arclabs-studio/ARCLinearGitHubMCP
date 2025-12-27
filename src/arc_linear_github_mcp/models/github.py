"""Pydantic models for GitHub API entities."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PRState(str, Enum):
    """Pull request state."""

    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"


class Repository(BaseModel):
    """GitHub repository model."""

    id: int
    name: str
    full_name: str
    description: str | None = None
    html_url: str
    default_branch: str
    private: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for MCP response."""
        return {
            "id": self.id,
            "name": self.name,
            "full_name": self.full_name,
            "description": self.description,
            "url": self.html_url,
            "default_branch": self.default_branch,
            "private": self.private,
        }


class GitUser(BaseModel):
    """GitHub user model."""

    login: str
    id: int
    avatar_url: str | None = None
    html_url: str | None = None


class Branch(BaseModel):
    """GitHub branch model."""

    name: str
    sha: str | None = Field(None, description="Commit SHA")
    protected: bool = False
    commit_url: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for MCP response."""
        return {
            "name": self.name,
            "sha": self.sha,
            "protected": self.protected,
        }


class BranchRef(BaseModel):
    """GitHub branch reference model."""

    ref: str
    sha: str
    url: str | None = None


class PullRequest(BaseModel):
    """GitHub pull request model."""

    id: int
    number: int
    title: str
    body: str | None = None
    state: str
    html_url: str
    head: BranchRef
    base: BranchRef
    user: GitUser | None = None
    draft: bool = False
    merged: bool = False
    mergeable: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    merged_at: datetime | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for MCP response."""
        return {
            "number": self.number,
            "title": self.title,
            "body": self.body,
            "state": self.state,
            "url": self.html_url,
            "head_branch": self.head.ref,
            "base_branch": self.base.ref,
            "author": self.user.login if self.user else None,
            "draft": self.draft,
            "merged": self.merged,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CreateBranchRequest(BaseModel):
    """Request model for creating a GitHub branch."""

    repo: str = Field(..., description="Repository name")
    branch_type: str = Field(
        ...,
        description="Branch type: feature, bugfix, hotfix, docs, spike, release",
    )
    issue_id: str | None = Field(
        None,
        description="Linear issue ID (e.g., FAVRES-123)",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Short description for branch name",
    )
    base_branch: str | None = Field(
        None,
        description="Base branch to create from (defaults to repo default branch)",
    )


class CreatePRRequest(BaseModel):
    """Request model for creating a GitHub pull request."""

    repo: str = Field(..., description="Repository name")
    branch: str = Field(..., description="Head branch name")
    base_branch: str | None = Field(
        None,
        description="Base branch (defaults to repo default branch)",
    )
    title: str = Field(..., min_length=1, max_length=256)
    body: str | None = Field(None, max_length=65536)
    issue_id: str | None = Field(
        None,
        description="Linear issue ID to link in PR",
    )
    draft: bool = Field(default=False, description="Create as draft PR")


class Commit(BaseModel):
    """GitHub commit model."""

    sha: str
    message: str
    author: GitUser | None = None
    html_url: str | None = None
    committed_date: datetime | None = None


class GitRef(BaseModel):
    """GitHub Git reference model."""

    ref: str
    object_sha: str = Field(..., alias="object")
    url: str | None = None
