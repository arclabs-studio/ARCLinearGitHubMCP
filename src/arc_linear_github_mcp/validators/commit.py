"""Commit message validation following Conventional Commits.

Commit format:
    <type>(<scope>): <subject>

Types: feat, fix, docs, style, refactor, perf, test, chore, build, ci, revert

Examples:
    - feat(search): add restaurant filtering
    - fix(map): resolve annotation crash
    - docs(readme): update installation steps
    - refactor: simplify auth flow
"""

import re
from dataclasses import dataclass

from arc_linear_github_mcp.config.standards import (
    COMMIT_PATTERN,
    COMMIT_TYPE_DESCRIPTIONS,
    COMMIT_TYPES,
)


@dataclass
class CommitValidationResult:
    """Result of commit message validation."""

    is_valid: bool
    commit_type: str | None = None
    scope: str | None = None
    subject: str | None = None
    error: str | None = None
    suggestions: list[str] | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for MCP response."""
        return {
            "is_valid": self.is_valid,
            "commit_type": self.commit_type,
            "scope": self.scope,
            "subject": self.subject,
            "error": self.error,
            "suggestions": self.suggestions,
        }


def validate_commit_message(message: str) -> CommitValidationResult:
    """Validate a commit message against Conventional Commits format.

    Args:
        message: The commit message to validate (first line only)

    Returns:
        CommitValidationResult with validation details
    """
    if not message:
        return CommitValidationResult(
            is_valid=False,
            error="Commit message cannot be empty",
        )

    # Get first line only
    first_line = message.split("\n")[0].strip()

    if not first_line:
        return CommitValidationResult(
            is_valid=False,
            error="Commit message cannot be empty",
        )

    # Check length
    if len(first_line) > 100:
        return CommitValidationResult(
            is_valid=False,
            error=f"Commit message too long ({len(first_line)} chars). Maximum is 100 characters.",
        )

    # Try to match the pattern
    match = re.match(COMMIT_PATTERN, first_line)

    if not match:
        suggestions = _generate_suggestions(first_line)
        error = _get_error_message(first_line)

        return CommitValidationResult(
            is_valid=False,
            error=error,
            suggestions=suggestions,
        )

    commit_type = match.group(1)
    scope = match.group(2)
    subject = match.group(3)

    # Validate subject doesn't start with capital
    if subject and subject[0].isupper():
        return CommitValidationResult(
            is_valid=False,
            commit_type=commit_type,
            scope=scope,
            subject=subject,
            error="Subject should start with lowercase letter",
            suggestions=[f"{commit_type}({scope}): {subject[0].lower()}{subject[1:]}" if scope else f"{commit_type}: {subject[0].lower()}{subject[1:]}"],
        )

    # Validate subject doesn't end with period
    if subject and subject.endswith("."):
        return CommitValidationResult(
            is_valid=False,
            commit_type=commit_type,
            scope=scope,
            subject=subject,
            error="Subject should not end with a period",
            suggestions=[f"{commit_type}({scope}): {subject[:-1]}" if scope else f"{commit_type}: {subject[:-1]}"],
        )

    return CommitValidationResult(
        is_valid=True,
        commit_type=commit_type,
        scope=scope,
        subject=subject,
    )


def parse_commit_message(message: str) -> tuple[str | None, str | None, str | None]:
    """Parse a commit message into its components.

    Args:
        message: The commit message to parse

    Returns:
        Tuple of (commit_type, scope, subject)
    """
    result = validate_commit_message(message)
    return result.commit_type, result.scope, result.subject


def generate_commit_message(
    commit_type: str,
    subject: str,
    scope: str | None = None,
) -> str:
    """Generate a valid commit message following Conventional Commits.

    Args:
        commit_type: Type of commit (feat, fix, docs, etc.)
        subject: The commit subject/description
        scope: Optional scope of the commit

    Returns:
        A valid commit message

    Raises:
        ValueError: If commit_type is invalid or subject is empty
    """
    if commit_type not in COMMIT_TYPES:
        raise ValueError(
            f"Invalid commit type '{commit_type}'. Valid types: {', '.join(sorted(COMMIT_TYPES))}"
        )

    if not subject:
        raise ValueError("Subject cannot be empty")

    # Normalize subject
    normalized_subject = subject.strip()

    # Ensure lowercase first letter
    if normalized_subject[0].isupper():
        normalized_subject = normalized_subject[0].lower() + normalized_subject[1:]

    # Remove trailing period
    if normalized_subject.endswith("."):
        normalized_subject = normalized_subject[:-1]

    # Build commit message
    if scope:
        return f"{commit_type}({scope}): {normalized_subject}"
    else:
        return f"{commit_type}: {normalized_subject}"


def get_commit_type_description(commit_type: str) -> str | None:
    """Get the description for a commit type.

    Args:
        commit_type: The commit type

    Returns:
        Description string or None if type is invalid
    """
    return COMMIT_TYPE_DESCRIPTIONS.get(commit_type)


def _get_error_message(message: str) -> str:
    """Generate a helpful error message for an invalid commit."""
    # Check if it has a colon
    if ":" not in message:
        return "Commit message must follow format: <type>(<scope>): <subject>"

    parts = message.split(":", 1)
    type_part = parts[0].strip()

    # Check for type with optional scope
    type_match = re.match(r"^(\w+)(?:\(([^)]+)\))?$", type_part)

    if not type_match:
        return "Invalid format before colon. Expected: <type> or <type>(<scope>)"

    potential_type = type_match.group(1)

    if potential_type not in COMMIT_TYPES:
        return f"Invalid commit type '{potential_type}'. Valid types: {', '.join(sorted(COMMIT_TYPES))}"

    # Subject issues
    if len(parts) > 1:
        subject = parts[1].strip()
        if not subject:
            return "Subject cannot be empty after the colon"

    return "Commit message format is invalid. Expected: <type>(<scope>): <subject>"


def _generate_suggestions(message: str) -> list[str]:
    """Generate suggestions for fixing an invalid commit message."""
    suggestions: list[str] = []

    # Try to extract the actual message
    # Remove common prefixes
    cleaned = message.strip()

    # Check for common patterns and try to fix them
    for commit_type in COMMIT_TYPES:
        if cleaned.lower().startswith(commit_type):
            rest = cleaned[len(commit_type):].strip()
            if rest.startswith(":"):
                rest = rest[1:].strip()
            if rest.startswith("-"):
                rest = rest[1:].strip()
            if rest:
                # Normalize subject
                subject = rest[0].lower() + rest[1:] if rest else rest
                if subject.endswith("."):
                    subject = subject[:-1]
                suggestions.append(f"{commit_type}: {subject}")
                break

    # If no type detected, try to guess from content
    if not suggestions:
        lower_message = message.lower()

        if any(word in lower_message for word in ["add", "new", "create", "implement"]):
            suggestions.append(f"feat: {_normalize_subject(message)}")
        elif any(word in lower_message for word in ["fix", "bug", "issue", "resolve"]):
            suggestions.append(f"fix: {_normalize_subject(message)}")
        elif any(word in lower_message for word in ["doc", "readme", "comment"]):
            suggestions.append(f"docs: {_normalize_subject(message)}")
        elif any(word in lower_message for word in ["refactor", "clean", "simplify"]):
            suggestions.append(f"refactor: {_normalize_subject(message)}")
        else:
            suggestions.append(f"chore: {_normalize_subject(message)}")

    return suggestions[:3]


def _normalize_subject(message: str) -> str:
    """Normalize a message to be used as a subject."""
    # Remove any existing type prefixes
    for commit_type in COMMIT_TYPES:
        if message.lower().startswith(commit_type):
            message = message[len(commit_type):].strip()
            if message.startswith(":"):
                message = message[1:].strip()
            break

    # Normalize
    if message:
        message = message[0].lower() + message[1:]
    if message.endswith("."):
        message = message[:-1]

    return message
