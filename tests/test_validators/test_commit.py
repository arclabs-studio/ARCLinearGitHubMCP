"""Tests for commit message validation."""

import pytest

from arc_linear_github_mcp.validators.commit import (
    generate_commit_message,
    parse_commit_message,
    validate_commit_message,
)


class TestValidateCommitMessage:
    """Tests for validate_commit_message function."""

    def test_valid_feat_with_scope(self) -> None:
        """Test valid feat commit with scope."""
        result = validate_commit_message("feat(search): add restaurant filtering")

        assert result.is_valid
        assert result.commit_type == "feat"
        assert result.scope == "search"
        assert result.subject == "add restaurant filtering"
        assert result.error is None

    def test_valid_fix_with_scope(self) -> None:
        """Test valid fix commit with scope."""
        result = validate_commit_message("fix(map): resolve annotation crash")

        assert result.is_valid
        assert result.commit_type == "fix"
        assert result.scope == "map"
        assert result.subject == "resolve annotation crash"

    def test_valid_docs_with_scope(self) -> None:
        """Test valid docs commit with scope."""
        result = validate_commit_message("docs(readme): update installation steps")

        assert result.is_valid
        assert result.commit_type == "docs"
        assert result.scope == "readme"

    def test_valid_refactor_without_scope(self) -> None:
        """Test valid refactor commit without scope."""
        result = validate_commit_message("refactor: simplify auth flow")

        assert result.is_valid
        assert result.commit_type == "refactor"
        assert result.scope is None
        assert result.subject == "simplify auth flow"

    def test_valid_all_commit_types(self) -> None:
        """Test all valid commit types."""
        commit_types = [
            "feat", "fix", "docs", "style", "refactor",
            "perf", "test", "chore", "build", "ci", "revert",
        ]

        for commit_type in commit_types:
            result = validate_commit_message(f"{commit_type}: test message")
            assert result.is_valid, f"Type '{commit_type}' should be valid"
            assert result.commit_type == commit_type

    def test_invalid_empty_message(self) -> None:
        """Test empty commit message."""
        result = validate_commit_message("")

        assert not result.is_valid
        assert result.error == "Commit message cannot be empty"

    def test_invalid_no_colon(self) -> None:
        """Test commit without colon."""
        result = validate_commit_message("feat add something")

        assert not result.is_valid
        assert "format" in result.error.lower()

    def test_invalid_unknown_type(self) -> None:
        """Test commit with unknown type."""
        result = validate_commit_message("unknown: some message")

        assert not result.is_valid
        assert "Invalid commit type 'unknown'" in result.error

    def test_invalid_uppercase_subject(self) -> None:
        """Test commit with uppercase subject."""
        result = validate_commit_message("feat: Add new feature")

        assert not result.is_valid
        assert "lowercase" in result.error.lower()
        assert result.suggestions is not None

    def test_invalid_trailing_period(self) -> None:
        """Test commit with trailing period."""
        result = validate_commit_message("feat: add new feature.")

        assert not result.is_valid
        assert "period" in result.error.lower()
        assert result.suggestions is not None

    def test_invalid_too_long(self) -> None:
        """Test commit message that's too long."""
        long_subject = "a" * 100
        result = validate_commit_message(f"feat: {long_subject}")

        assert not result.is_valid
        assert "too long" in result.error.lower()

    def test_multiline_uses_first_line(self) -> None:
        """Test that only first line is validated."""
        result = validate_commit_message("feat: add feature\n\nThis is a longer description")

        assert result.is_valid
        assert result.subject == "add feature"

    def test_suggestions_for_invalid(self) -> None:
        """Test that suggestions are provided for invalid messages."""
        result = validate_commit_message("Added new feature")

        assert not result.is_valid
        assert result.suggestions is not None
        assert len(result.suggestions) > 0


class TestParseCommitMessage:
    """Tests for parse_commit_message function."""

    def test_parse_full_message(self) -> None:
        """Test parsing a complete commit message."""
        commit_type, scope, subject = parse_commit_message(
            "feat(search): add restaurant filtering"
        )

        assert commit_type == "feat"
        assert scope == "search"
        assert subject == "add restaurant filtering"

    def test_parse_message_without_scope(self) -> None:
        """Test parsing message without scope."""
        commit_type, scope, subject = parse_commit_message("fix: resolve crash")

        assert commit_type == "fix"
        assert scope is None
        assert subject == "resolve crash"

    def test_parse_invalid_message(self) -> None:
        """Test parsing invalid message returns None values."""
        commit_type, scope, subject = parse_commit_message("invalid message")

        assert commit_type is None
        assert scope is None
        assert subject is None


class TestGenerateCommitMessage:
    """Tests for generate_commit_message function."""

    def test_generate_with_scope(self) -> None:
        """Test generating commit message with scope."""
        result = generate_commit_message(
            commit_type="feat",
            subject="add restaurant filtering",
            scope="search",
        )

        assert result == "feat(search): add restaurant filtering"

    def test_generate_without_scope(self) -> None:
        """Test generating commit message without scope."""
        result = generate_commit_message(
            commit_type="fix",
            subject="resolve crash",
        )

        assert result == "fix: resolve crash"

    def test_generate_normalizes_subject(self) -> None:
        """Test that subject is normalized (lowercase first letter, no trailing period)."""
        result = generate_commit_message(
            commit_type="feat",
            subject="Add New Feature.",
        )

        # Only first letter is lowercased, trailing period removed
        assert result == "feat: add New Feature"

    def test_generate_invalid_type_raises(self) -> None:
        """Test that invalid type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid commit type"):
            generate_commit_message(
                commit_type="invalid",
                subject="test",
            )

    def test_generate_empty_subject_raises(self) -> None:
        """Test that empty subject raises ValueError."""
        with pytest.raises(ValueError, match="Subject cannot be empty"):
            generate_commit_message(
                commit_type="feat",
                subject="",
            )

    def test_generate_all_types(self) -> None:
        """Test generating with all valid types."""
        commit_types = [
            "feat", "fix", "docs", "style", "refactor",
            "perf", "test", "chore", "build", "ci", "revert",
        ]

        for commit_type in commit_types:
            result = generate_commit_message(
                commit_type=commit_type,
                subject="test message",
            )
            assert result.startswith(f"{commit_type}:")
