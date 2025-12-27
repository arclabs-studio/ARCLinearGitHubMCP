"""MCP tools for combined Linear + GitHub workflows."""

from mcp.server.fastmcp import FastMCP

from arc_linear_github_mcp.clients.github import GitHubClient, GitHubClientError
from arc_linear_github_mcp.clients.linear import LinearClient, LinearClientError
from arc_linear_github_mcp.config.settings import get_settings
from arc_linear_github_mcp.config.standards import BRANCH_TYPES, COMMIT_TYPES
from arc_linear_github_mcp.models.linear import CreateIssueRequest
from arc_linear_github_mcp.validators.branch import (
    generate_branch_name,
    validate_branch_name,
)
from arc_linear_github_mcp.validators.commit import (
    generate_commit_message,
    validate_commit_message,
)


def register_workflow_tools(mcp: FastMCP) -> None:
    """Register combined workflow MCP tools.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    async def workflow_start_feature(
        title: str,
        description: str | None = None,
        repo: str | None = None,
        project: str = "FAVRES",
        priority: int = 3,
        branch_type: str = "feature",
    ) -> dict:
        """Start a new feature workflow: create Linear issue and GitHub branch.

        This is a convenience tool that combines:
        1. Creates a new issue in Linear
        2. Creates a properly named branch in GitHub

        Args:
            title: Feature title (used for both issue and branch)
            description: Optional description for the Linear issue
            repo: GitHub repository name (defaults to configured default)
            project: Linear project/team key (default: 'FAVRES')
            priority: Issue priority (1=Urgent, 2=High, 3=Normal, 4=Low)
            branch_type: Type of branch (default: 'feature')

        Returns:
            Dictionary with created issue and branch details
        """
        settings = get_settings()
        linear_client = LinearClient(settings)
        github_client = GitHubClient(settings)
        repo = repo or settings.default_repo

        result = {
            "success": False,
            "issue": None,
            "branch": None,
            "next_steps": [],
        }

        try:
            # Step 1: Create Linear issue
            team = await linear_client.get_team_by_key(project)
            if not team:
                return {
                    "success": False,
                    "error": f"Team/project '{project}' not found",
                }

            request = CreateIssueRequest(
                title=title,
                description=description,
                team_id=team.id,
                priority=priority,
            )

            issue = await linear_client.create_issue(request)
            result["issue"] = issue.to_dict()

            # Step 2: Create GitHub branch
            branch_name = generate_branch_name(
                branch_type=branch_type,
                description=title,
                issue_id=issue.identifier,
            )

            # Check if branch exists
            existing = await github_client.get_branch(repo, branch_name)
            if existing:
                result["success"] = True
                result["branch"] = {
                    "name": branch_name,
                    "already_exists": True,
                }
                result["message"] = f"Issue {issue.identifier} created. Branch '{branch_name}' already exists."
            else:
                branch = await github_client.create_branch(repo, branch_name)
                result["branch"] = branch.to_dict()
                result["success"] = True
                result["message"] = f"Created issue {issue.identifier} and branch '{branch_name}'"

            # Add next steps
            result["next_steps"] = [
                f"git fetch origin",
                f"git checkout {branch_name}",
                f"# Start working on your feature",
                f"# When ready, create a PR linking to {issue.identifier}",
            ]

            return result

        except LinearClientError as e:
            return {
                "success": False,
                "error": f"Linear error: {e}",
                "issue": result.get("issue"),
            }
        except GitHubClientError as e:
            return {
                "success": False,
                "error": f"GitHub error: {e}",
                "issue": result.get("issue"),
                "message": "Issue was created but branch creation failed",
            }
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            await linear_client.close()
            await github_client.close()

    @mcp.tool()
    async def workflow_validate_branch_name(branch_name: str) -> dict:
        """Validate a branch name against ARC Labs conventions.

        Args:
            branch_name: The branch name to validate

        Returns:
            Dictionary with validation result and details

        Valid branch format: <type>/<issue-id>-<description>
        Types: feature, bugfix, hotfix, docs, spike, release
        Examples:
            - feature/FAVRES-123-restaurant-search
            - bugfix/FAVRES-456-map-crash
            - docs/update-readme
        """
        result = validate_branch_name(branch_name)

        response = result.to_dict()
        response["valid_types"] = sorted(BRANCH_TYPES)

        if result.is_valid:
            response["message"] = f"Valid {result.branch_type} branch"
            if result.issue_id:
                response["message"] += f" for issue {result.issue_id}"
        else:
            response["message"] = f"Invalid branch name: {result.error}"

        return response

    @mcp.tool()
    async def workflow_validate_commit_message(message: str) -> dict:
        """Validate a commit message against Conventional Commits format.

        Args:
            message: The commit message to validate

        Returns:
            Dictionary with validation result and details

        Valid commit format: <type>(<scope>): <subject>
        Types: feat, fix, docs, style, refactor, perf, test, chore, build, ci, revert
        Examples:
            - feat(search): add restaurant filtering
            - fix(map): resolve annotation crash
            - docs(readme): update installation steps
        """
        result = validate_commit_message(message)

        response = result.to_dict()
        response["valid_types"] = sorted(COMMIT_TYPES)

        if result.is_valid:
            response["message"] = f"Valid {result.commit_type} commit"
            if result.scope:
                response["message"] += f" with scope '{result.scope}'"
        else:
            response["message"] = f"Invalid commit message: {result.error}"

        return response

    @mcp.tool()
    async def workflow_generate_branch_name(
        branch_type: str,
        description: str,
        issue_id: str | None = None,
    ) -> dict:
        """Generate a valid branch name following ARC Labs conventions.

        Args:
            branch_type: Type of branch (feature, bugfix, hotfix, docs, spike, release)
            description: Short description for the branch
            issue_id: Optional Linear issue ID (e.g., 'FAVRES-123')

        Returns:
            Dictionary with generated branch name

        Examples:
            - branch_type='feature', issue_id='FAVRES-123', description='restaurant search'
              -> 'feature/FAVRES-123-restaurant-search'
            - branch_type='docs', description='Update README'
              -> 'docs/update-readme'
        """
        try:
            branch_name = generate_branch_name(
                branch_type=branch_type,
                description=description,
                issue_id=issue_id,
            )

            return {
                "success": True,
                "branch_name": branch_name,
                "components": {
                    "type": branch_type,
                    "issue_id": issue_id,
                    "description": description,
                },
            }
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "valid_types": sorted(BRANCH_TYPES),
            }

    @mcp.tool()
    async def workflow_generate_commit_message(
        commit_type: str,
        subject: str,
        scope: str | None = None,
    ) -> dict:
        """Generate a valid commit message following Conventional Commits.

        Args:
            commit_type: Type of commit (feat, fix, docs, etc.)
            subject: The commit subject/description
            scope: Optional scope of the commit

        Returns:
            Dictionary with generated commit message

        Examples:
            - commit_type='feat', scope='search', subject='Add restaurant filtering'
              -> 'feat(search): add restaurant filtering'
            - commit_type='fix', subject='Resolve annotation crash'
              -> 'fix: resolve annotation crash'
        """
        try:
            message = generate_commit_message(
                commit_type=commit_type,
                subject=subject,
                scope=scope,
            )

            return {
                "success": True,
                "commit_message": message,
                "components": {
                    "type": commit_type,
                    "scope": scope,
                    "subject": subject,
                },
            }
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "valid_types": sorted(COMMIT_TYPES),
            }

    @mcp.tool()
    async def workflow_get_conventions() -> dict:
        """Get ARC Labs naming conventions reference.

        Returns a reference of all naming conventions used by ARC Labs Studio.
        """
        return {
            "branch_naming": {
                "format": "<type>/<issue-id>-<description>",
                "types": sorted(BRANCH_TYPES),
                "examples": [
                    "feature/FAVRES-123-restaurant-search",
                    "bugfix/FAVRES-456-map-crash",
                    "hotfix/FAVRES-789-auth-fix",
                    "docs/update-readme",
                    "spike/swiftui-animations",
                    "release/1.2.0",
                ],
            },
            "commit_format": {
                "format": "<type>(<scope>): <subject>",
                "types": sorted(COMMIT_TYPES),
                "examples": [
                    "feat(search): add restaurant filtering",
                    "fix(map): resolve annotation crash",
                    "docs(readme): update installation steps",
                    "refactor: simplify auth flow",
                ],
                "rules": [
                    "Subject should be lowercase",
                    "No period at the end of subject",
                    "Maximum 100 characters for first line",
                    "Use imperative mood (add, fix, update, not added, fixed, updated)",
                ],
            },
            "pr_naming": {
                "format": "<Type>/<Issue-ID>: <Title>",
                "examples": [
                    "Feature/FAVRES-123: Restaurant Search Implementation",
                    "Bugfix/FAVRES-456: Map Annotation Crash Fix",
                    "Hotfix/FAVRES-789: Authentication Token Refresh",
                ],
            },
            "linear_priority": {
                "1": "Urgent",
                "2": "High",
                "3": "Normal (default)",
                "4": "Low",
            },
        }
