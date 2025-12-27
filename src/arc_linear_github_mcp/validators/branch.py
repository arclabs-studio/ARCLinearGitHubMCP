"""Branch name validation following ARC Labs conventions.

Branch naming format:
    <type>/<issue-id>-<short-description>

Examples:
    - feature/FAVRES-123-restaurant-search
    - bugfix/FAVRES-456-map-crash
    - hotfix/FAVRES-789-auth-fix
    - docs/update-readme
    - spike/swiftui-animations
    - release/1.2.0
"""

import re
from dataclasses import dataclass

from arc_linear_github_mcp.config.standards import (
    BRANCH_PATTERN,
    BRANCH_TYPES,
    ISSUE_ID_PATTERN,
)


@dataclass
class BranchValidationResult:
    """Result of branch name validation."""

    is_valid: bool
    branch_type: str | None = None
    issue_id: str | None = None
    description: str | None = None
    error: str | None = None
    suggestions: list[str] | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for MCP response."""
        return {
            "is_valid": self.is_valid,
            "branch_type": self.branch_type,
            "issue_id": self.issue_id,
            "description": self.description,
            "error": self.error,
            "suggestions": self.suggestions,
        }


def validate_branch_name(branch_name: str) -> BranchValidationResult:
    """Validate a branch name against ARC Labs conventions.

    Args:
        branch_name: The branch name to validate

    Returns:
        BranchValidationResult with validation details
    """
    if not branch_name:
        return BranchValidationResult(
            is_valid=False,
            error="Branch name cannot be empty",
        )

    # Check for reserved names
    reserved_names = {"main", "master", "develop", "HEAD"}
    if branch_name in reserved_names:
        return BranchValidationResult(
            is_valid=False,
            error=f"'{branch_name}' is a reserved branch name",
        )

    # Try to match the pattern
    match = re.match(BRANCH_PATTERN, branch_name)

    if not match:
        # Provide helpful error message
        suggestions = _generate_suggestions(branch_name)

        # Check if it has a slash
        if "/" not in branch_name:
            error = "Branch name must include a type prefix (e.g., feature/, bugfix/)"
        elif branch_name.split("/")[0] not in BRANCH_TYPES:
            branch_type = branch_name.split("/")[0]
            error = f"Invalid branch type '{branch_type}'. Valid types: {', '.join(sorted(BRANCH_TYPES))}"
        else:
            error = "Branch name format is invalid. Expected: <type>/<issue-id>-<description> or <type>/<description>"

        return BranchValidationResult(
            is_valid=False,
            error=error,
            suggestions=suggestions,
        )

    branch_type = match.group(1)
    issue_id = match.group(2)
    description = match.group(3)

    return BranchValidationResult(
        is_valid=True,
        branch_type=branch_type,
        issue_id=issue_id,
        description=description,
    )


def parse_branch_name(branch_name: str) -> tuple[str | None, str | None, str | None]:
    """Parse a branch name into its components.

    Args:
        branch_name: The branch name to parse

    Returns:
        Tuple of (branch_type, issue_id, description)
    """
    result = validate_branch_name(branch_name)
    return result.branch_type, result.issue_id, result.description


def generate_branch_name(
    branch_type: str,
    description: str,
    issue_id: str | None = None,
) -> str:
    """Generate a valid branch name following ARC Labs conventions.

    Args:
        branch_type: Type of branch (feature, bugfix, hotfix, docs, spike, release)
        description: Short description of the branch
        issue_id: Optional Linear issue ID (e.g., FAVRES-123)

    Returns:
        A valid branch name

    Raises:
        ValueError: If branch_type is invalid or description is empty
    """
    # Validate branch type
    if branch_type not in BRANCH_TYPES:
        raise ValueError(
            f"Invalid branch type '{branch_type}'. Valid types: {', '.join(sorted(BRANCH_TYPES))}"
        )

    if not description:
        raise ValueError("Description cannot be empty")

    # Validate issue ID format if provided
    if issue_id and not re.match(ISSUE_ID_PATTERN, issue_id):
        raise ValueError(
            f"Invalid issue ID format '{issue_id}'. Expected format: PROJECT-123"
        )

    # Normalize description
    normalized_description = _normalize_description(description)

    if not normalized_description:
        raise ValueError("Description must contain at least one valid character")

    # Build branch name
    if issue_id:
        return f"{branch_type}/{issue_id}-{normalized_description}"
    else:
        return f"{branch_type}/{normalized_description}"


def _normalize_description(description: str) -> str:
    """Normalize a description for use in a branch name.

    - Converts to lowercase
    - Replaces spaces and underscores with hyphens
    - Removes invalid characters
    - Collapses multiple hyphens
    - Trims leading/trailing hyphens
    """
    # Convert to lowercase
    normalized = description.lower()

    # Replace spaces and underscores with hyphens
    normalized = re.sub(r"[\s_]+", "-", normalized)

    # Remove invalid characters (keep only alphanumeric and hyphens)
    normalized = re.sub(r"[^a-z0-9-]", "", normalized)

    # Collapse multiple hyphens
    normalized = re.sub(r"-+", "-", normalized)

    # Trim leading/trailing hyphens
    normalized = normalized.strip("-")

    return normalized


def _generate_suggestions(branch_name: str) -> list[str]:
    """Generate suggestions for fixing an invalid branch name."""
    suggestions: list[str] = []

    # Extract potential parts
    parts = branch_name.replace("_", "/").replace(" ", "/").split("/")

    if len(parts) >= 2:
        potential_type = parts[0].lower()
        rest = "-".join(parts[1:])

        # Try to match to a valid type
        for valid_type in BRANCH_TYPES:
            if potential_type.startswith(valid_type[:3]):
                normalized = _normalize_description(rest)
                if normalized:
                    suggestions.append(f"{valid_type}/{normalized}")
                break

    # If no type detected, suggest common types
    if not suggestions:
        normalized = _normalize_description(branch_name)
        if normalized:
            suggestions.append(f"feature/{normalized}")
            suggestions.append(f"bugfix/{normalized}")

    return suggestions[:3]  # Limit to 3 suggestions
