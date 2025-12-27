# CLAUDE.md - Context for Claude Code

This file provides context for Claude Code when working with the ARCLinearGitHubMCP project.

## Project Overview

ARCLinearGitHubMCP is an MCP (Model Context Protocol) Server that integrates Linear (issue tracking) and GitHub (repository management) for ARC Labs Studio. It enforces naming conventions and automates development workflows.

## Tech Stack

- **Language**: Python 3.12+
- **MCP Framework**: FastMCP (`mcp[cli]`)
- **Package Manager**: uv
- **Linear API**: GraphQL via `gql[httpx]`
- **GitHub API**: REST via `httpx`
- **Validation**: Pydantic v2

## Key Files

### Entry Point
- `src/arc_linear_github_mcp/server.py` - FastMCP server initialization and tool registration

### Configuration
- `src/arc_linear_github_mcp/config/settings.py` - Pydantic Settings for environment variables
- `src/arc_linear_github_mcp/config/standards.py` - ARC Labs naming conventions and constants

### API Clients
- `src/arc_linear_github_mcp/clients/linear.py` - Async GraphQL client for Linear API
- `src/arc_linear_github_mcp/clients/github.py` - Async REST client for GitHub API

### MCP Tools
- `src/arc_linear_github_mcp/tools/linear.py` - Linear-specific MCP tools
- `src/arc_linear_github_mcp/tools/github.py` - GitHub-specific MCP tools
- `src/arc_linear_github_mcp/tools/workflow.py` - Combined workflow tools

### Validators
- `src/arc_linear_github_mcp/validators/branch.py` - Branch name validation
- `src/arc_linear_github_mcp/validators/commit.py` - Commit message validation

### Models
- `src/arc_linear_github_mcp/models/linear.py` - Pydantic models for Linear entities
- `src/arc_linear_github_mcp/models/github.py` - Pydantic models for GitHub entities

## Common Commands

```bash
# Install dependencies
uv sync

# Run in development mode with inspector
uv run mcp dev src/arc_linear_github_mcp/server.py

# Run directly
uv run python -m arc_linear_github_mcp.server

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=arc_linear_github_mcp

# Lint and format
uv run ruff check .
uv run ruff format .

# Install in Claude Desktop
uv run mcp install src/arc_linear_github_mcp/server.py --name "ARC Workflow"
```

## Naming Conventions (ARC Labs Standards)

### Branch Names
Format: `<type>/<issue-id>-<description>`
- Types: `feature`, `bugfix`, `hotfix`, `docs`, `spike`, `release`
- Example: `feature/FAVRES-123-restaurant-search`

### Commit Messages
Format: `<type>(<scope>): <subject>`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `build`, `ci`, `revert`
- Example: `feat(search): add restaurant filtering`

### PR Titles
Format: `<Type>/<Issue-ID>: <Title>`
- Example: `Feature/FAVRES-123: Restaurant Search Implementation`

## Environment Variables

Required in `.env`:
```
LINEAR_API_KEY=lin_api_xxxxx
GITHUB_TOKEN=ghp_xxxxx
GITHUB_ORG=arclabs-studio
DEFAULT_PROJECT=FAVRES
DEFAULT_REPO=FavRes
```

## Architecture Notes

### MCP Tool Pattern
Tools are registered via decorator functions that receive the FastMCP instance:
```python
def register_linear_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def linear_list_issues(...) -> dict:
        ...
```

### Client Pattern
All API clients are async and should be properly closed:
```python
client = LinearClient(settings)
try:
    result = await client.list_issues(...)
finally:
    await client.close()
```

### Validation Pattern
Validators return result dataclasses with `is_valid`, parsed components, and error/suggestions:
```python
result = validate_branch_name("feature/FAVRES-123-test")
if result.is_valid:
    print(result.branch_type, result.issue_id, result.description)
else:
    print(result.error, result.suggestions)
```

## Testing

- Tests use pytest with async support
- Mock environment variables are set in `conftest.py`
- Validators have comprehensive unit tests
- API clients would need mocking for integration tests

## Adding New Tools

1. Add the tool function in the appropriate `tools/*.py` file
2. Use `@mcp.tool()` decorator
3. Include proper type hints and docstrings
4. Return a dictionary with `success` boolean and relevant data or `error`
5. Handle exceptions and always close clients

## Error Handling

All tools return dictionaries with:
- `success: bool` - Whether the operation succeeded
- `error: str` - Error message if failed
- Operation-specific data if succeeded

## Linear API Notes

- GraphQL endpoint: `https://api.linear.app/graphql`
- Authentication: Bearer token in Authorization header
- Team key (e.g., "FAVRES") is used to identify projects
- Issue identifiers are formatted as `TEAM-NUMBER` (e.g., FAVRES-123)

## GitHub API Notes

- REST API endpoint: `https://api.github.com`
- Authentication: Bearer token
- Repository paths use org/repo format
- Branch creation requires getting base branch SHA first
