# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-12-22

### Added

- Initial release of ARCLinearGitHubMCP
- Linear API integration with GraphQL client
  - `linear_list_issues` - List issues from a project
  - `linear_get_issue` - Get issue details
  - `linear_create_issue` - Create new issues
  - `linear_update_issue` - Update existing issues
  - `linear_list_states` - List workflow states
  - `linear_list_labels` - List project labels
- GitHub API integration with REST client
  - `github_list_branches` - List repository branches
  - `github_create_branch` - Create branches with ARC naming
  - `github_list_prs` - List pull requests
  - `github_create_pr` - Create PRs with ARC template
  - `github_get_pr` - Get PR details
  - `github_get_default_branch` - Get default branch
- Workflow automation tools
  - `workflow_start_feature` - Create issue + branch combo
  - `workflow_validate_branch_name` - Validate branch names
  - `workflow_validate_commit_message` - Validate commits
  - `workflow_generate_branch_name` - Generate valid branch names
  - `workflow_generate_commit_message` - Generate valid commits
  - `workflow_get_conventions` - Get naming conventions reference
- ARC Labs naming convention enforcement
  - Branch naming: `<type>/<issue-id>-<description>`
  - Commit messages: `<type>(<scope>): <subject>`
  - PR titles: `<Type>/<Issue-ID>: <Title>`
- Pydantic models for type-safe API interactions
- Comprehensive test suite for validators
- Full documentation with README.md and CLAUDE.md
