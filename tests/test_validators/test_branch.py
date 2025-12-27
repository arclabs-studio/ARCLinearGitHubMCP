"""Tests for branch name validation."""

import pytest

from arc_linear_github_mcp.validators.branch import (
    generate_branch_name,
    parse_branch_name,
    validate_branch_name,
)


class TestValidateBranchName:
    """Tests for validate_branch_name function."""

    def test_valid_feature_branch_with_issue(self) -> None:
        """Test valid feature branch with issue ID."""
        result = validate_branch_name("feature/FAVRES-123-restaurant-search")

        assert result.is_valid
        assert result.branch_type == "feature"
        assert result.issue_id == "FAVRES-123"
        assert result.description == "restaurant-search"
        assert result.error is None

    def test_valid_bugfix_branch_with_issue(self) -> None:
        """Test valid bugfix branch with issue ID."""
        result = validate_branch_name("bugfix/FAVRES-456-map-crash")

        assert result.is_valid
        assert result.branch_type == "bugfix"
        assert result.issue_id == "FAVRES-456"
        assert result.description == "map-crash"

    def test_valid_hotfix_branch(self) -> None:
        """Test valid hotfix branch."""
        result = validate_branch_name("hotfix/FAVRES-789-auth-fix")

        assert result.is_valid
        assert result.branch_type == "hotfix"
        assert result.issue_id == "FAVRES-789"

    def test_valid_docs_branch_without_issue(self) -> None:
        """Test valid docs branch without issue ID."""
        result = validate_branch_name("docs/update-readme")

        assert result.is_valid
        assert result.branch_type == "docs"
        assert result.issue_id is None
        assert result.description == "update-readme"

    def test_valid_spike_branch(self) -> None:
        """Test valid spike branch."""
        result = validate_branch_name("spike/swiftui-animations")

        assert result.is_valid
        assert result.branch_type == "spike"
        assert result.issue_id is None
        assert result.description == "swiftui-animations"

    def test_valid_release_branch(self) -> None:
        """Test valid release branch."""
        result = validate_branch_name("release/1-2-0")

        assert result.is_valid
        assert result.branch_type == "release"
        assert result.description == "1-2-0"

    def test_invalid_empty_branch(self) -> None:
        """Test empty branch name."""
        result = validate_branch_name("")

        assert not result.is_valid
        assert result.error == "Branch name cannot be empty"

    def test_invalid_reserved_name_main(self) -> None:
        """Test reserved branch name 'main'."""
        result = validate_branch_name("main")

        assert not result.is_valid
        assert "'main' is a reserved branch name" in result.error

    def test_invalid_reserved_name_master(self) -> None:
        """Test reserved branch name 'master'."""
        result = validate_branch_name("master")

        assert not result.is_valid
        assert "'master' is a reserved branch name" in result.error

    def test_invalid_no_type_prefix(self) -> None:
        """Test branch without type prefix."""
        result = validate_branch_name("my-branch")

        assert not result.is_valid
        assert "type prefix" in result.error

    def test_invalid_unknown_type(self) -> None:
        """Test branch with unknown type."""
        result = validate_branch_name("unknown/some-branch")

        assert not result.is_valid
        assert "Invalid branch type 'unknown'" in result.error

    def test_invalid_uppercase_description(self) -> None:
        """Test branch with uppercase in description."""
        result = validate_branch_name("feature/FAVRES-123-RestaurantSearch")

        assert not result.is_valid

    def test_suggestions_provided(self) -> None:
        """Test that suggestions are provided for invalid names."""
        result = validate_branch_name("my feature branch")

        assert not result.is_valid
        assert result.suggestions is not None
        assert len(result.suggestions) > 0


class TestParseBranchName:
    """Tests for parse_branch_name function."""

    def test_parse_full_branch(self) -> None:
        """Test parsing a complete branch name."""
        branch_type, issue_id, description = parse_branch_name(
            "feature/FAVRES-123-restaurant-search"
        )

        assert branch_type == "feature"
        assert issue_id == "FAVRES-123"
        assert description == "restaurant-search"

    def test_parse_branch_without_issue(self) -> None:
        """Test parsing branch without issue ID."""
        branch_type, issue_id, description = parse_branch_name("docs/update-readme")

        assert branch_type == "docs"
        assert issue_id is None
        assert description == "update-readme"

    def test_parse_invalid_branch(self) -> None:
        """Test parsing invalid branch returns None values."""
        branch_type, issue_id, description = parse_branch_name("invalid")

        assert branch_type is None
        assert issue_id is None
        assert description is None


class TestGenerateBranchName:
    """Tests for generate_branch_name function."""

    def test_generate_with_issue_id(self) -> None:
        """Test generating branch name with issue ID."""
        result = generate_branch_name(
            branch_type="feature",
            description="restaurant search",
            issue_id="FAVRES-123",
        )

        assert result == "feature/FAVRES-123-restaurant-search"

    def test_generate_without_issue_id(self) -> None:
        """Test generating branch name without issue ID."""
        result = generate_branch_name(
            branch_type="docs",
            description="update readme",
        )

        assert result == "docs/update-readme"

    def test_generate_normalizes_description(self) -> None:
        """Test that description is normalized."""
        result = generate_branch_name(
            branch_type="feature",
            description="Add Restaurant Search Feature!",
            issue_id="FAVRES-123",
        )

        assert result == "feature/FAVRES-123-add-restaurant-search-feature"

    def test_generate_invalid_type_raises(self) -> None:
        """Test that invalid type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid branch type"):
            generate_branch_name(
                branch_type="invalid",
                description="test",
            )

    def test_generate_empty_description_raises(self) -> None:
        """Test that empty description raises ValueError."""
        with pytest.raises(ValueError, match="Description cannot be empty"):
            generate_branch_name(
                branch_type="feature",
                description="",
            )

    def test_generate_invalid_issue_id_raises(self) -> None:
        """Test that invalid issue ID format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid issue ID format"):
            generate_branch_name(
                branch_type="feature",
                description="test",
                issue_id="invalid-id",
            )

    def test_generate_handles_special_characters(self) -> None:
        """Test that special characters are handled."""
        result = generate_branch_name(
            branch_type="feature",
            description="add @mentions & #hashtags!",
        )

        assert result == "feature/add-mentions-hashtags"

    def test_generate_collapses_hyphens(self) -> None:
        """Test that multiple hyphens are collapsed."""
        result = generate_branch_name(
            branch_type="feature",
            description="fix---multiple---hyphens",
        )

        assert result == "feature/fix-multiple-hyphens"
