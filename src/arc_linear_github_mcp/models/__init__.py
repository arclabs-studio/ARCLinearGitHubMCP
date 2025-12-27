"""Pydantic models for Linear and GitHub entities."""

from arc_linear_github_mcp.models.github import (
    Branch,
    CreateBranchRequest,
    CreatePRRequest,
    PullRequest,
    Repository,
)
from arc_linear_github_mcp.models.linear import (
    CreateIssueRequest,
    Issue,
    IssueState,
    Priority,
    Project,
    UpdateIssueRequest,
    User,
)

__all__ = [
    # Linear models
    "Issue",
    "Project",
    "User",
    "IssueState",
    "Priority",
    "CreateIssueRequest",
    "UpdateIssueRequest",
    # GitHub models
    "Repository",
    "Branch",
    "PullRequest",
    "CreateBranchRequest",
    "CreatePRRequest",
]
