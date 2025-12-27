"""GitHub REST API client."""

from typing import Any

import httpx

from arc_linear_github_mcp.config.settings import Settings
from arc_linear_github_mcp.models.github import Branch, Commit, PullRequest, Repository


class GitHubClientError(Exception):
    """Exception raised for GitHub API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class GitHubClient:
    """Async client for GitHub REST API."""

    def __init__(self, settings: Settings):
        """Initialize GitHub client.

        Args:
            settings: Application settings containing API token
        """
        self.settings = settings
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.settings.github_api_url,
                headers={
                    "Authorization": f"Bearer {self.settings.github_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=self.settings.request_timeout,
            )
        return self._client

    async def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict | list:
        """Make an HTTP request to GitHub API.

        Args:
            method: HTTP method
            path: API path
            json: Request body
            params: Query parameters

        Returns:
            Response data

        Raises:
            GitHubClientError: If the request fails
        """
        client = await self._get_client()
        try:
            response = await client.request(method, path, json=json, params=params)

            if response.status_code == 404:
                raise GitHubClientError(f"Not found: {path}", status_code=404)
            if response.status_code == 422:
                error_data = response.json()
                message = error_data.get("message", "Validation failed")
                errors = error_data.get("errors", [])
                if errors:
                    message += f": {errors}"
                raise GitHubClientError(message, status_code=422)
            if response.status_code >= 400:
                raise GitHubClientError(
                    f"GitHub API error: {response.status_code} - {response.text}",
                    status_code=response.status_code,
                )

            if response.status_code == 204:
                return {}

            return response.json()
        except httpx.HTTPError as e:
            raise GitHubClientError(f"HTTP error: {e}") from e

    def _repo_path(self, repo: str) -> str:
        """Get the full repository path.

        Args:
            repo: Repository name (will be prefixed with org if needed)

        Returns:
            Full path like 'orgs/arclabs-studio/repos/FavRes' or 'repos/owner/repo'
        """
        if "/" in repo:
            return f"/repos/{repo}"
        return f"/repos/{self.settings.github_org}/{repo}"

    async def get_repository(self, repo: str) -> Repository:
        """Get repository information.

        Args:
            repo: Repository name

        Returns:
            Repository information
        """
        path = self._repo_path(repo)
        data = await self._request("GET", path)
        return Repository(**data)

    async def list_branches(self, repo: str, per_page: int = 100) -> list[Branch]:
        """List branches in a repository.

        Args:
            repo: Repository name
            per_page: Number of branches per page

        Returns:
            List of branches
        """
        path = f"{self._repo_path(repo)}/branches"
        data = await self._request("GET", path, params={"per_page": per_page})

        branches = []
        for item in data:
            branches.append(
                Branch(
                    name=item["name"],
                    sha=item["commit"]["sha"] if "commit" in item else None,
                    protected=item.get("protected", False),
                )
            )
        return branches

    async def get_branch(self, repo: str, branch: str) -> Branch | None:
        """Get a specific branch.

        Args:
            repo: Repository name
            branch: Branch name

        Returns:
            Branch if found, None otherwise
        """
        try:
            path = f"{self._repo_path(repo)}/branches/{branch}"
            data = await self._request("GET", path)
            return Branch(
                name=data["name"],
                sha=data["commit"]["sha"] if "commit" in data else None,
                protected=data.get("protected", False),
            )
        except GitHubClientError as e:
            if e.status_code == 404:
                return None
            raise

    async def create_branch(
        self,
        repo: str,
        branch_name: str,
        base_branch: str | None = None,
    ) -> Branch:
        """Create a new branch.

        Args:
            repo: Repository name
            branch_name: New branch name
            base_branch: Base branch to create from (defaults to repo default)

        Returns:
            Created branch

        Raises:
            GitHubClientError: If creation fails
        """
        # Get the base branch SHA
        if base_branch is None:
            repository = await self.get_repository(repo)
            base_branch = repository.default_branch

        base = await self.get_branch(repo, base_branch)
        if not base:
            raise GitHubClientError(f"Base branch '{base_branch}' not found")

        # Create the reference
        path = f"{self._repo_path(repo)}/git/refs"
        data = await self._request(
            "POST",
            path,
            json={
                "ref": f"refs/heads/{branch_name}",
                "sha": base.sha,
            },
        )

        return Branch(
            name=branch_name,
            sha=data.get("object", {}).get("sha"),
            protected=False,
        )

    async def delete_branch(self, repo: str, branch_name: str) -> bool:
        """Delete a branch.

        Args:
            repo: Repository name
            branch_name: Branch to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            path = f"{self._repo_path(repo)}/git/refs/heads/{branch_name}"
            await self._request("DELETE", path)
            return True
        except GitHubClientError as e:
            if e.status_code == 404:
                return False
            raise

    async def list_pull_requests(
        self,
        repo: str,
        state: str = "open",
        per_page: int = 30,
    ) -> list[PullRequest]:
        """List pull requests in a repository.

        Args:
            repo: Repository name
            state: PR state ('open', 'closed', 'all')
            per_page: Number of PRs per page

        Returns:
            List of pull requests
        """
        path = f"{self._repo_path(repo)}/pulls"
        data = await self._request(
            "GET",
            path,
            params={"state": state, "per_page": per_page},
        )

        prs = []
        for item in data:
            prs.append(self._parse_pr(item))
        return prs

    async def get_pull_request(self, repo: str, pr_number: int) -> PullRequest | None:
        """Get a specific pull request.

        Args:
            repo: Repository name
            pr_number: PR number

        Returns:
            PullRequest if found, None otherwise
        """
        try:
            path = f"{self._repo_path(repo)}/pulls/{pr_number}"
            data = await self._request("GET", path)
            return self._parse_pr(data)
        except GitHubClientError as e:
            if e.status_code == 404:
                return None
            raise

    async def create_pull_request(
        self,
        repo: str,
        title: str,
        head: str,
        base: str | None = None,
        body: str | None = None,
        draft: bool = False,
    ) -> PullRequest:
        """Create a new pull request.

        Args:
            repo: Repository name
            title: PR title
            head: Head branch name
            base: Base branch (defaults to repo default)
            body: PR description
            draft: Create as draft PR

        Returns:
            Created pull request

        Raises:
            GitHubClientError: If creation fails
        """
        if base is None:
            repository = await self.get_repository(repo)
            base = repository.default_branch

        path = f"{self._repo_path(repo)}/pulls"
        request_body: dict[str, Any] = {
            "title": title,
            "head": head,
            "base": base,
            "draft": draft,
        }
        if body:
            request_body["body"] = body

        data = await self._request("POST", path, json=request_body)
        return self._parse_pr(data)

    async def update_pull_request(
        self,
        repo: str,
        pr_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
    ) -> PullRequest:
        """Update an existing pull request.

        Args:
            repo: Repository name
            pr_number: PR number
            title: New title
            body: New description
            state: New state ('open', 'closed')

        Returns:
            Updated pull request
        """
        path = f"{self._repo_path(repo)}/pulls/{pr_number}"
        request_body: dict[str, Any] = {}

        if title is not None:
            request_body["title"] = title
        if body is not None:
            request_body["body"] = body
        if state is not None:
            request_body["state"] = state

        data = await self._request("PATCH", path, json=request_body)
        return self._parse_pr(data)

    async def get_default_branch(self, repo: str) -> str:
        """Get the default branch for a repository.

        Args:
            repo: Repository name

        Returns:
            Default branch name
        """
        repository = await self.get_repository(repo)
        return repository.default_branch

    async def list_commits(
        self,
        repo: str,
        branch: str | None = None,
        per_page: int = 30,
    ) -> list[Commit]:
        """List commits in a repository.

        Args:
            repo: Repository name
            branch: Branch name (defaults to default branch)
            per_page: Number of commits per page

        Returns:
            List of commits
        """
        path = f"{self._repo_path(repo)}/commits"
        params: dict[str, Any] = {"per_page": per_page}
        if branch:
            params["sha"] = branch

        data = await self._request("GET", path, params=params)

        commits = []
        for item in data:
            commits.append(
                Commit(
                    sha=item["sha"],
                    message=item["commit"]["message"],
                    html_url=item.get("html_url"),
                )
            )
        return commits

    def _parse_pr(self, data: dict) -> PullRequest:
        """Parse pull request data from API response."""
        from arc_linear_github_mcp.models.github import BranchRef, GitUser

        head = BranchRef(
            ref=data["head"]["ref"],
            sha=data["head"]["sha"],
            url=data["head"].get("repo", {}).get("html_url") if data["head"].get("repo") else None,
        )
        base = BranchRef(
            ref=data["base"]["ref"],
            sha=data["base"]["sha"],
            url=data["base"].get("repo", {}).get("html_url") if data["base"].get("repo") else None,
        )

        user = None
        if data.get("user"):
            user = GitUser(
                login=data["user"]["login"],
                id=data["user"]["id"],
                avatar_url=data["user"].get("avatar_url"),
                html_url=data["user"].get("html_url"),
            )

        return PullRequest(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            body=data.get("body"),
            state=data["state"],
            html_url=data["html_url"],
            head=head,
            base=base,
            user=user,
            draft=data.get("draft", False),
            merged=data.get("merged", False),
            mergeable=data.get("mergeable"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            merged_at=data.get("merged_at"),
        )

    async def close(self) -> None:
        """Close the client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
