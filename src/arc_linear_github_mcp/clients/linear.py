"""Linear GraphQL API client."""

from typing import Any

import httpx
from gql import Client, gql
from gql.transport.httpx import HTTPXAsyncTransport

from arc_linear_github_mcp.config.settings import Settings
from arc_linear_github_mcp.models.linear import (
    CreateIssueRequest,
    Issue,
    IssueState,
    Label,
    Project,
    Team,
    UpdateIssueRequest,
    User,
    WorkflowState,
)


class LinearClientError(Exception):
    """Exception raised for Linear API errors."""

    def __init__(self, message: str, errors: list[dict] | None = None):
        super().__init__(message)
        self.errors = errors or []


class LinearClient:
    """Async client for Linear GraphQL API."""

    def __init__(self, settings: Settings):
        """Initialize Linear client.

        Args:
            settings: Application settings containing API key
        """
        self.settings = settings
        self._client: Client | None = None

    async def _get_client(self) -> Client:
        """Get or create the GraphQL client."""
        if self._client is None:
            transport = HTTPXAsyncTransport(
                url=self.settings.linear_api_url,
                headers={
                    "Authorization": self.settings.linear_api_key,
                    "Content-Type": "application/json",
                },
                timeout=self.settings.request_timeout,
            )
            self._client = Client(
                transport=transport,
                fetch_schema_from_transport=False,
            )
        return self._client

    async def _execute(self, query: str, variables: dict[str, Any] | None = None) -> dict:
        """Execute a GraphQL query.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Query result data

        Raises:
            LinearClientError: If the query fails
        """
        client = await self._get_client()
        try:
            async with client as session:
                result = await session.execute(gql(query), variable_values=variables)
                return result
        except Exception as e:
            raise LinearClientError(f"Linear API error: {e}") from e

    async def get_viewer(self) -> User:
        """Get the authenticated user.

        Returns:
            The authenticated user
        """
        query = """
            query Viewer {
                viewer {
                    id
                    name
                    email
                    displayName
                }
            }
        """
        result = await self._execute(query)
        return User(**result["viewer"])

    async def list_teams(self) -> list[Team]:
        """List all teams the user has access to.

        Returns:
            List of teams
        """
        query = """
            query Teams {
                teams {
                    nodes {
                        id
                        name
                        key
                    }
                }
            }
        """
        result = await self._execute(query)
        return [Team(**team) for team in result["teams"]["nodes"]]

    async def get_team_by_key(self, key: str) -> Team | None:
        """Get a team by its key (e.g., 'FAVRES').

        Args:
            key: Team key

        Returns:
            Team if found, None otherwise
        """
        teams = await self.list_teams()
        for team in teams:
            if team.key.upper() == key.upper():
                return team
        return None

    async def list_workflow_states(self, team_id: str) -> list[WorkflowState]:
        """List workflow states for a team.

        Args:
            team_id: Linear team ID

        Returns:
            List of workflow states
        """
        query = """
            query WorkflowStates($teamId: String!) {
                workflowStates(filter: { team: { id: { eq: $teamId } } }) {
                    nodes {
                        id
                        name
                        type
                        color
                    }
                }
            }
        """
        result = await self._execute(query, {"teamId": team_id})
        return [WorkflowState(**state) for state in result["workflowStates"]["nodes"]]

    async def get_state_by_name(self, team_id: str, state_name: str) -> WorkflowState | None:
        """Get a workflow state by name.

        Args:
            team_id: Linear team ID
            state_name: State name (e.g., 'In Progress')

        Returns:
            WorkflowState if found, None otherwise
        """
        states = await self.list_workflow_states(team_id)
        for state in states:
            if state.name.lower() == state_name.lower():
                return state
        return None

    async def list_issues(
        self,
        team_key: str,
        state: str | None = None,
        first: int = 50,
    ) -> list[Issue]:
        """List issues for a team/project.

        Args:
            team_key: Team key (e.g., 'FAVRES')
            state: Optional state filter (e.g., 'In Progress')
            first: Number of issues to fetch

        Returns:
            List of issues
        """
        # Build filter
        filter_parts = [f'team: {{ key: {{ eq: "{team_key}" }} }}']
        if state:
            filter_parts.append(f'state: {{ name: {{ eq: "{state}" }} }}')

        filter_str = ", ".join(filter_parts)

        query = f"""
            query Issues($first: Int!) {{
                issues(first: $first, filter: {{ {filter_str} }}) {{
                    nodes {{
                        id
                        identifier
                        title
                        description
                        priority
                        priorityLabel
                        url
                        createdAt
                        updatedAt
                        state {{
                            id
                            name
                            type
                            color
                        }}
                        assignee {{
                            id
                            name
                            email
                        }}
                        labels {{
                            nodes {{
                                id
                                name
                                color
                            }}
                        }}
                    }}
                }}
            }}
        """
        result = await self._execute(query, {"first": first})

        issues = []
        for node in result["issues"]["nodes"]:
            # Flatten labels
            if "labels" in node and "nodes" in node["labels"]:
                node["labels"] = node["labels"]["nodes"]
            issues.append(Issue(**node))

        return issues

    async def get_issue(self, issue_id: str) -> Issue | None:
        """Get a specific issue by identifier (e.g., 'FAVRES-123').

        Args:
            issue_id: Issue identifier

        Returns:
            Issue if found, None otherwise
        """
        query = """
            query Issue($id: String!) {
                issue(id: $id) {
                    id
                    identifier
                    title
                    description
                    priority
                    priorityLabel
                    url
                    createdAt
                    updatedAt
                    state {
                        id
                        name
                        type
                        color
                    }
                    assignee {
                        id
                        name
                        email
                    }
                    labels {
                        nodes {
                            id
                            name
                            color
                        }
                    }
                    team {
                        id
                        name
                        key
                    }
                }
            }
        """
        try:
            result = await self._execute(query, {"id": issue_id})
            if result.get("issue"):
                node = result["issue"]
                if "labels" in node and "nodes" in node["labels"]:
                    node["labels"] = node["labels"]["nodes"]
                return Issue(**node)
            return None
        except LinearClientError:
            return None

    async def search_issue_by_identifier(self, identifier: str) -> Issue | None:
        """Search for an issue by its identifier (e.g., 'FAVRES-123').

        Args:
            identifier: Issue identifier

        Returns:
            Issue if found, None otherwise
        """
        query = """
            query IssueByIdentifier($filter: IssueFilter!) {
                issues(filter: $filter, first: 1) {
                    nodes {
                        id
                        identifier
                        title
                        description
                        priority
                        priorityLabel
                        url
                        createdAt
                        updatedAt
                        state {
                            id
                            name
                            type
                            color
                        }
                        assignee {
                            id
                            name
                            email
                        }
                        labels {
                            nodes {
                                id
                                name
                                color
                            }
                        }
                        team {
                            id
                            name
                            key
                        }
                    }
                }
            }
        """
        # Parse identifier to get team key and number
        if "-" in identifier:
            parts = identifier.split("-")
            team_key = parts[0]
            number = int(parts[1])

            result = await self._execute(
                query,
                {
                    "filter": {
                        "team": {"key": {"eq": team_key}},
                        "number": {"eq": number},
                    }
                },
            )

            if result["issues"]["nodes"]:
                node = result["issues"]["nodes"][0]
                if "labels" in node and "nodes" in node["labels"]:
                    node["labels"] = node["labels"]["nodes"]
                return Issue(**node)

        return None

    async def create_issue(self, request: CreateIssueRequest) -> Issue:
        """Create a new issue.

        Args:
            request: Issue creation request

        Returns:
            Created issue

        Raises:
            LinearClientError: If creation fails
        """
        mutation = """
            mutation CreateIssue($input: IssueCreateInput!) {
                issueCreate(input: $input) {
                    success
                    issue {
                        id
                        identifier
                        title
                        description
                        priority
                        priorityLabel
                        url
                        createdAt
                        updatedAt
                        state {
                            id
                            name
                            type
                            color
                        }
                        team {
                            id
                            name
                            key
                        }
                    }
                }
            }
        """
        input_data: dict[str, Any] = {
            "title": request.title,
            "teamId": request.team_id,
            "priority": request.priority,
        }

        if request.description:
            input_data["description"] = request.description
        if request.project_id:
            input_data["projectId"] = request.project_id
        if request.assignee_id:
            input_data["assigneeId"] = request.assignee_id
        if request.state_id:
            input_data["stateId"] = request.state_id
        if request.label_ids:
            input_data["labelIds"] = request.label_ids

        result = await self._execute(mutation, {"input": input_data})

        if not result["issueCreate"]["success"]:
            raise LinearClientError("Failed to create issue")

        return Issue(**result["issueCreate"]["issue"])

    async def update_issue(self, issue_id: str, request: UpdateIssueRequest) -> Issue:
        """Update an existing issue.

        Args:
            issue_id: Linear issue ID (internal UUID)
            request: Update request

        Returns:
            Updated issue

        Raises:
            LinearClientError: If update fails
        """
        mutation = """
            mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
                issueUpdate(id: $id, input: $input) {
                    success
                    issue {
                        id
                        identifier
                        title
                        description
                        priority
                        priorityLabel
                        url
                        createdAt
                        updatedAt
                        state {
                            id
                            name
                            type
                            color
                        }
                        assignee {
                            id
                            name
                            email
                        }
                        labels {
                            nodes {
                                id
                                name
                                color
                            }
                        }
                    }
                }
            }
        """
        input_data: dict[str, Any] = {}

        if request.title is not None:
            input_data["title"] = request.title
        if request.description is not None:
            input_data["description"] = request.description
        if request.priority is not None:
            input_data["priority"] = request.priority
        if request.state_id is not None:
            input_data["stateId"] = request.state_id
        if request.assignee_id is not None:
            input_data["assigneeId"] = request.assignee_id
        if request.label_ids is not None:
            input_data["labelIds"] = request.label_ids

        result = await self._execute(mutation, {"id": issue_id, "input": input_data})

        if not result["issueUpdate"]["success"]:
            raise LinearClientError("Failed to update issue")

        node = result["issueUpdate"]["issue"]
        if "labels" in node and "nodes" in node["labels"]:
            node["labels"] = node["labels"]["nodes"]

        return Issue(**node)

    async def list_labels(self, team_id: str) -> list[Label]:
        """List labels for a team.

        Args:
            team_id: Linear team ID

        Returns:
            List of labels
        """
        query = """
            query Labels($teamId: String!) {
                issueLabels(filter: { team: { id: { eq: $teamId } } }) {
                    nodes {
                        id
                        name
                        color
                    }
                }
            }
        """
        result = await self._execute(query, {"teamId": team_id})
        return [Label(**label) for label in result["issueLabels"]["nodes"]]

    async def list_users(self) -> list[User]:
        """List all users in the workspace.

        Returns:
            List of users
        """
        query = """
            query Users {
                users {
                    nodes {
                        id
                        name
                        email
                        displayName
                    }
                }
            }
        """
        result = await self._execute(query)
        return [User(**user) for user in result["users"]["nodes"]]

    async def close(self) -> None:
        """Close the client connection."""
        self._client = None
