# 📄 ARCLinearGitHubMCP

MCP Server for integrating Linear and GitHub following ARC Labs Studio standards.

## Overview

This MCP (Model Context Protocol) Server enables Claude (Desktop and Code) to interact with Linear and GitHub, automating development workflows while enforcing ARC Labs naming conventions.

## Features

- **Linear Integration**: Create, list, and update issues
- **GitHub Integration**: Create branches and PRs with proper naming
- **Workflow Automation**: Combined tools for starting features
- **Naming Validation**: Validate branch names and commit messages
- **Convention Enforcement**: Automatic formatting following ARC Labs standards

## Installation

### Prerequisites

- Python 3.12+
- uv (recommended) or pip
- Linear API key
- GitHub Personal Access Token

### Setup

1. Clone the repository:
```bash
git clone https://github.com/arclabs-studio/ARCLinearGitHubMCP.git
cd ARCLinearGitHubMCP
```

2. Install dependencies:
```bash
uv sync
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Claude Desktop Integration

Install the MCP server in Claude Desktop:
```bash
uv run mcp install src/arc_linear_github_mcp/server.py --name "ARC Workflow"
```

Or add to your Claude Desktop configuration manually:
```json
{
  "mcpServers": {
    "arc-workflow": {
      "command": "uv",
      "args": ["run", "python", "-m", "arc_linear_github_mcp.server"],
      "cwd": "/path/to/ARCLinearGitHubMCP"
    }
  }
}
```

## Configuration

Create a `.env` file with:

```bash
# Linear API
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxx

# GitHub API
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
GITHUB_ORG=arclabs-studio

# Defaults
DEFAULT_PROJECT=FAVRES
DEFAULT_REPO=FavRes
```

## Available Tools

### Linear Tools

| Tool | Description |
|------|-------------|
| `linear_list_issues` | List issues from a Linear project |
| `linear_get_issue` | Get details of a specific issue |
| `linear_create_issue` | Create a new issue |
| `linear_update_issue` | Update an existing issue |
| `linear_list_states` | List available workflow states |
| `linear_list_labels` | List available labels |

### GitHub Tools

| Tool | Description |
|------|-------------|
| `github_list_branches` | List branches in a repository |
| `github_create_branch` | Create a branch with ARC naming |
| `github_list_prs` | List pull requests |
| `github_create_pr` | Create a PR with ARC template |
| `github_get_pr` | Get PR details |
| `github_get_default_branch` | Get default branch name |

### Workflow Tools

| Tool | Description |
|------|-------------|
| `workflow_start_feature` | Create issue + branch in one step |
| `workflow_validate_branch_name` | Validate branch name |
| `workflow_validate_commit_message` | Validate commit message |
| `workflow_generate_branch_name` | Generate valid branch name |
| `workflow_generate_commit_message` | Generate valid commit |
| `workflow_get_conventions` | Get naming conventions reference |

## ARC Labs Naming Conventions

### Branch Naming

Format: `<type>/<issue-id>-<short-description>`

**Types**: `feature`, `bugfix`, `hotfix`, `docs`, `spike`, `release`

**Examples**:
- `feature/FAVRES-123-restaurant-search`
- `bugfix/FAVRES-456-map-crash`
- `hotfix/FAVRES-789-auth-fix`
- `docs/update-readme`
- `spike/swiftui-animations`
- `release/1.2.0`

### Commit Messages

Format: `<type>(<scope>): <subject>`

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `build`, `ci`, `revert`

**Examples**:
- `feat(search): add restaurant filtering`
- `fix(map): resolve annotation crash`
- `docs(readme): update installation steps`

### PR Naming

Format: `<Type>/<Issue-ID>: <Title>`

**Examples**:
- `Feature/FAVRES-123: Restaurant Search Implementation`
- `Bugfix/FAVRES-456: Map Annotation Crash Fix`

## Development

### Running in Development Mode

```bash
# With MCP Inspector
uv run mcp dev src/arc_linear_github_mcp/server.py

# Directly
uv run python -m arc_linear_github_mcp.server
```

### Running Tests

```bash
uv run pytest

# With coverage
uv run pytest --cov=arc_linear_github_mcp
```

### Linting

```bash
uv run ruff check .
uv run ruff format .
```

## Project Structure

```
ARCLinearGitHubMCP/
├── src/arc_linear_github_mcp/
│   ├── __init__.py
│   ├── server.py              # FastMCP server
│   ├── config/
│   │   ├── settings.py        # Environment configuration
│   │   └── standards.py       # Naming conventions
│   ├── clients/
│   │   ├── linear.py          # Linear GraphQL client
│   │   └── github.py          # GitHub REST client
│   ├── tools/
│   │   ├── linear.py          # Linear MCP tools
│   │   ├── github.py          # GitHub MCP tools
│   │   └── workflow.py        # Combined workflow tools
│   ├── validators/
│   │   ├── branch.py          # Branch name validator
│   │   └── commit.py          # Commit message validator
│   └── models/
│       ├── linear.py          # Linear Pydantic models
│       └── github.py          # GitHub Pydantic models
└── tests/
    ├── conftest.py
    └── test_validators/
        ├── test_branch.py
        └── test_commit.py
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Create a feature branch following naming conventions
2. Make changes with proper commit messages
3. Create a PR using the ARC Labs template

## Support

For issues or feature requests, please open an issue on GitHub.
