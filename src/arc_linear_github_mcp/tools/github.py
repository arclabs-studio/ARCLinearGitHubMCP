"""MCP tools for GitHub API integration."""

from mcp.server.fastmcp import FastMCP

from arc_linear_github_mcp.clients.github import GitHubClient, GitHubClientError
from arc_linear_github_mcp.config.settings import get_settings
from arc_linear_github_mcp.config.standards import BRANCH_TO_PR_PREFIX
from arc_linear_github_mcp.validators.branch import generate_branch_name, validate_branch_name


def register_github_tools(mcp: FastMCP) -> None:
    """Register GitHub-related MCP tools.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    async def github_list_branches(repo: str | None = None, limit: int = 100) -> dict:
        """List branches in a GitHub repository.

        Args:
            repo: Repository name (defaults to configured default repo)
            limit: Maximum number of branches to return

        Returns:
            Dictionary with list of branches
        """
        settings = get_settings()
        client = GitHubClient(settings)
        repo = repo or settings.default_repo

        try:
            branches = await client.list_branches(repo, per_page=limit)

            return {
                "success": True,
                "repository": f"{settings.github_org}/{repo}",
                "count": len(branches),
                "branches": [branch.to_dict() for branch in branches],
            }
        except GitHubClientError as e:
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            await client.close()

    @mcp.tool()
    async def github_create_branch(
        branch_type: str,
        description: str,
        issue_id: str | None = None,
        repo: str | None = None,
        base_branch: str | None = None,
    ) -> dict:
        """Create a branch following ARC Labs naming conventions.

        Args:
            branch_type: Type of branch (feature, bugfix, hotfix, docs, spike, release)
            description: Short description for the branch name
            issue_id: Optional Linear issue ID (e.g., 'FAVRES-123')
            repo: Repository name (defaults to configured default repo)
            base_branch: Base branch to create from (defaults to repo default branch)

        Returns:
            Dictionary with created branch details or error

        Example branch names:
            - feature/FAVRES-123-restaurant-search
            - bugfix/FAVRES-456-map-crash
            - docs/update-readme
        """
        settings = get_settings()
        client = GitHubClient(settings)
        repo = repo or settings.default_repo

        try:
            # Generate the branch name
            branch_name = generate_branch_name(
                branch_type=branch_type,
                description=description,
                issue_id=issue_id,
            )

            # Check if branch already exists
            existing = await client.get_branch(repo, branch_name)
            if existing:
                return {
                    "success": False,
                    "error": f"Branch '{branch_name}' already exists",
                    "branch_name": branch_name,
                }

            # Create the branch
            branch = await client.create_branch(repo, branch_name, base_branch)

            return {
                "success": True,
                "branch": branch.to_dict(),
                "branch_name": branch_name,
                "repository": f"{settings.github_org}/{repo}",
                "message": f"Created branch '{branch_name}'",
            }
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
            }
        except GitHubClientError as e:
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            await client.close()

    @mcp.tool()
    async def github_list_prs(
        repo: str | None = None,
        state: str = "open",
        limit: int = 30,
    ) -> dict:
        """List pull requests in a repository.

        Args:
            repo: Repository name (defaults to configured default repo)
            state: PR state filter ('open', 'closed', 'all')
            limit: Maximum number of PRs to return

        Returns:
            Dictionary with list of pull requests
        """
        settings = get_settings()
        client = GitHubClient(settings)
        repo = repo or settings.default_repo

        try:
            prs = await client.list_pull_requests(repo, state=state, per_page=limit)

            return {
                "success": True,
                "repository": f"{settings.github_org}/{repo}",
                "state": state,
                "count": len(prs),
                "pull_requests": [pr.to_dict() for pr in prs],
            }
        except GitHubClientError as e:
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            await client.close()

    @mcp.tool()
    async def github_create_pr(
        branch: str,
        title: str,
        body: str | None = None,
        issue_id: str | None = None,
        repo: str | None = None,
        base_branch: str | None = None,
        draft: bool = False,
    ) -> dict:
        """Create a pull request with ARC Labs template.

        Args:
            branch: Head branch name
            title: PR title (will be formatted with issue_id if provided)
            body: PR description (optional)
            issue_id: Linear issue ID to link (e.g., 'FAVRES-123')
            repo: Repository name (defaults to configured default repo)
            base_branch: Base branch (defaults to repo default branch)
            draft: Create as draft PR

        Returns:
            Dictionary with created PR details or error

        The PR title will be formatted as: '<Type>/<Issue-ID>: <Title>'
        Example: 'Feature/FAVRES-123: Restaurant Search Implementation'
        """
        settings = get_settings()
        client = GitHubClient(settings)
        repo = repo or settings.default_repo

        try:
            # Parse branch to get type for PR title prefix
            validation = validate_branch_name(branch)

            # Format the PR title
            if validation.is_valid and validation.branch_type:
                prefix = BRANCH_TO_PR_PREFIX.get(validation.branch_type, "Feature")
                if issue_id:
                    formatted_title = f"{prefix}/{issue_id}: {title}"
                elif validation.issue_id:
                    formatted_title = f"{prefix}/{validation.issue_id}: {title}"
                else:
                    formatted_title = f"{prefix}: {title}"
            else:
                formatted_title = title

            # Build PR body with Linear link if issue_id provided
            pr_body = body or ""
            if issue_id:
                linear_link = f"\n\n---\nLinear Issue: [{issue_id}](https://linear.app/issue/{issue_id})"
                pr_body = pr_body + linear_link if pr_body else f"Linear Issue: [{issue_id}](https://linear.app/issue/{issue_id})"

            # Create the PR
            pr = await client.create_pull_request(
                repo=repo,
                title=formatted_title,
                head=branch,
                base=base_branch,
                body=pr_body,
                draft=draft,
            )

            return {
                "success": True,
                "pull_request": pr.to_dict(),
                "url": pr.html_url,
                "message": f"Created PR #{pr.number}: {pr.title}",
            }
        except GitHubClientError as e:
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            await client.close()

    @mcp.tool()
    async def github_get_pr(pr_number: int, repo: str | None = None) -> dict:
        """Get details of a specific pull request.

        Args:
            pr_number: Pull request number
            repo: Repository name (defaults to configured default repo)

        Returns:
            Dictionary with PR details or error
        """
        settings = get_settings()
        client = GitHubClient(settings)
        repo = repo or settings.default_repo

        try:
            pr = await client.get_pull_request(repo, pr_number)

            if pr:
                return {
                    "success": True,
                    "pull_request": pr.to_dict(),
                }
            else:
                return {
                    "success": False,
                    "error": f"PR #{pr_number} not found",
                }
        except GitHubClientError as e:
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            await client.close()

    @mcp.tool()
    async def github_get_default_branch(repo: str | None = None) -> dict:
        """Get the default branch for a repository.

        Args:
            repo: Repository name (defaults to configured default repo)

        Returns:
            Dictionary with default branch name
        """
        settings = get_settings()
        client = GitHubClient(settings)
        repo = repo or settings.default_repo

        try:
            default_branch = await client.get_default_branch(repo)

            return {
                "success": True,
                "repository": f"{settings.github_org}/{repo}",
                "default_branch": default_branch,
            }
        except GitHubClientError as e:
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            await client.close()
