"""MCP tools for Linear API integration."""

from mcp.server.fastmcp import FastMCP

from arc_linear_github_mcp.clients.linear import LinearClient, LinearClientError
from arc_linear_github_mcp.config.settings import get_settings
from arc_linear_github_mcp.models.linear import CreateIssueRequest, UpdateIssueRequest


def register_linear_tools(mcp: FastMCP) -> None:
    """Register Linear-related MCP tools.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    async def linear_list_issues(
        project: str = "FAVRES",
        state: str | None = None,
        limit: int = 50,
    ) -> dict:
        """List issues from a Linear project.

        Args:
            project: Project/team key (e.g., 'FAVRES')
            state: Optional state filter (e.g., 'In Progress', 'Todo', 'Done')
            limit: Maximum number of issues to return (default: 50)

        Returns:
            Dictionary with list of issues and count
        """
        settings = get_settings()
        client = LinearClient(settings)

        try:
            issues = await client.list_issues(team_key=project, state=state, first=limit)

            return {
                "success": True,
                "count": len(issues),
                "issues": [issue.to_dict() for issue in issues],
            }
        except LinearClientError as e:
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            await client.close()

    @mcp.tool()
    async def linear_get_issue(issue_id: str) -> dict:
        """Get details of a specific Linear issue.

        Args:
            issue_id: Issue identifier (e.g., 'FAVRES-123')

        Returns:
            Dictionary with issue details or error
        """
        settings = get_settings()
        client = LinearClient(settings)

        try:
            issue = await client.search_issue_by_identifier(issue_id)

            if issue:
                return {
                    "success": True,
                    "issue": issue.to_dict(),
                }
            else:
                return {
                    "success": False,
                    "error": f"Issue '{issue_id}' not found",
                }
        except LinearClientError as e:
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            await client.close()

    @mcp.tool()
    async def linear_create_issue(
        title: str,
        description: str | None = None,
        project: str = "FAVRES",
        priority: int = 3,
        labels: list[str] | None = None,
    ) -> dict:
        """Create a new issue in Linear with ARC Labs format.

        Args:
            title: Issue title
            description: Optional issue description (supports Markdown)
            project: Project/team key (default: 'FAVRES')
            priority: Priority level (1=Urgent, 2=High, 3=Normal, 4=Low)
            labels: Optional list of label names to apply

        Returns:
            Dictionary with created issue details or error
        """
        settings = get_settings()
        client = LinearClient(settings)

        try:
            # Get team ID from project key
            team = await client.get_team_by_key(project)
            if not team:
                return {
                    "success": False,
                    "error": f"Team/project '{project}' not found",
                }

            # Resolve label IDs if provided
            label_ids: list[str] = []
            if labels:
                all_labels = await client.list_labels(team.id)
                label_map = {label.name.lower(): label.id for label in all_labels}

                for label_name in labels:
                    label_id = label_map.get(label_name.lower())
                    if label_id:
                        label_ids.append(label_id)

            # Create the issue
            request = CreateIssueRequest(
                title=title,
                description=description,
                team_id=team.id,
                priority=priority,
                label_ids=label_ids,
            )

            issue = await client.create_issue(request)

            return {
                "success": True,
                "issue": issue.to_dict(),
                "message": f"Created issue {issue.identifier}: {issue.title}",
            }
        except LinearClientError as e:
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            await client.close()

    @mcp.tool()
    async def linear_update_issue(
        issue_id: str,
        state: str | None = None,
        assignee: str | None = None,
        title: str | None = None,
        priority: int | None = None,
    ) -> dict:
        """Update an existing Linear issue.

        Args:
            issue_id: Issue identifier (e.g., 'FAVRES-123')
            state: New state name (e.g., 'In Progress', 'Done')
            assignee: Assignee name or email
            title: New title
            priority: New priority (1=Urgent, 2=High, 3=Normal, 4=Low)

        Returns:
            Dictionary with updated issue details or error
        """
        settings = get_settings()
        client = LinearClient(settings)

        try:
            # Find the issue first
            issue = await client.search_issue_by_identifier(issue_id)
            if not issue:
                return {
                    "success": False,
                    "error": f"Issue '{issue_id}' not found",
                }

            # Build update request
            update_data: dict = {}

            if title is not None:
                update_data["title"] = title

            if priority is not None:
                update_data["priority"] = priority

            # Resolve state ID if provided
            if state:
                if issue.team:
                    workflow_state = await client.get_state_by_name(issue.team.id, state)
                    if workflow_state:
                        update_data["state_id"] = workflow_state.id
                    else:
                        return {
                            "success": False,
                            "error": f"State '{state}' not found. Use linear_list_states to see available states.",
                        }

            # Resolve assignee ID if provided
            if assignee:
                users = await client.list_users()
                assignee_user = None
                for user in users:
                    if (
                        user.name.lower() == assignee.lower()
                        or (user.email and user.email.lower() == assignee.lower())
                    ):
                        assignee_user = user
                        break

                if assignee_user:
                    update_data["assignee_id"] = assignee_user.id
                else:
                    return {
                        "success": False,
                        "error": f"User '{assignee}' not found",
                    }

            if not update_data:
                return {
                    "success": False,
                    "error": "No updates provided",
                }

            request = UpdateIssueRequest(**update_data)
            updated_issue = await client.update_issue(issue.id, request)

            return {
                "success": True,
                "issue": updated_issue.to_dict(),
                "message": f"Updated issue {updated_issue.identifier}",
            }
        except LinearClientError as e:
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            await client.close()

    @mcp.tool()
    async def linear_list_states(project: str = "FAVRES") -> dict:
        """List available workflow states for a project.

        Args:
            project: Project/team key (default: 'FAVRES')

        Returns:
            Dictionary with list of states
        """
        settings = get_settings()
        client = LinearClient(settings)

        try:
            team = await client.get_team_by_key(project)
            if not team:
                return {
                    "success": False,
                    "error": f"Team/project '{project}' not found",
                }

            states = await client.list_workflow_states(team.id)

            return {
                "success": True,
                "states": [
                    {"id": s.id, "name": s.name, "type": s.type}
                    for s in states
                ],
            }
        except LinearClientError as e:
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            await client.close()

    @mcp.tool()
    async def linear_list_labels(project: str = "FAVRES") -> dict:
        """List available labels for a project.

        Args:
            project: Project/team key (default: 'FAVRES')

        Returns:
            Dictionary with list of labels
        """
        settings = get_settings()
        client = LinearClient(settings)

        try:
            team = await client.get_team_by_key(project)
            if not team:
                return {
                    "success": False,
                    "error": f"Team/project '{project}' not found",
                }

            labels = await client.list_labels(team.id)

            return {
                "success": True,
                "labels": [
                    {"id": label.id, "name": label.name, "color": label.color}
                    for label in labels
                ],
            }
        except LinearClientError as e:
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            await client.close()
