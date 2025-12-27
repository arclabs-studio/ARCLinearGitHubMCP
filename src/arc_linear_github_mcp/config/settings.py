"""Application settings using Pydantic Settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Linear API Configuration
    linear_api_key: str = Field(
        ...,
        description="Linear API key (lin_api_xxxxx)",
    )
    linear_api_url: str = Field(
        default="https://api.linear.app/graphql",
        description="Linear GraphQL API endpoint",
    )

    # GitHub API Configuration
    github_token: str = Field(
        ...,
        description="GitHub Personal Access Token (ghp_xxxxx)",
    )
    github_api_url: str = Field(
        default="https://api.github.com",
        description="GitHub REST API endpoint",
    )
    github_org: str = Field(
        default="arclabs-studio",
        description="GitHub organization name",
    )

    # Default Project Settings
    default_project: str = Field(
        default="FAVRES",
        description="Default Linear project key",
    )
    default_repo: str = Field(
        default="FavRes",
        description="Default GitHub repository name",
    )

    # Request Timeouts
    request_timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance
    """
    return Settings()
