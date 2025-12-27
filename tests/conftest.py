"""Pytest configuration and fixtures."""

import os

import pytest


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set mock environment variables for testing."""
    monkeypatch.setenv("LINEAR_API_KEY", "lin_api_test_key")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
    monkeypatch.setenv("GITHUB_ORG", "test-org")
    monkeypatch.setenv("DEFAULT_PROJECT", "TEST")
    monkeypatch.setenv("DEFAULT_REPO", "TestRepo")


@pytest.fixture
def clear_settings_cache() -> None:
    """Clear the settings LRU cache."""
    from arc_linear_github_mcp.config.settings import get_settings

    get_settings.cache_clear()
