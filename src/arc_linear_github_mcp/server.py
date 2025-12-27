"""ARCLinearGitHubMCP Server.

An MCP Server for integrating Linear and GitHub following ARC Labs Studio standards.
"""

from mcp.server.fastmcp import FastMCP

from arc_linear_github_mcp.tools.github import register_github_tools
from arc_linear_github_mcp.tools.linear import register_linear_tools
from arc_linear_github_mcp.tools.workflow import register_workflow_tools

# Create the FastMCP server
mcp = FastMCP(name="ARCLinearGitHubMCP Workflow")

# Register all tools
register_linear_tools(mcp)
register_github_tools(mcp)
register_workflow_tools(mcp)


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
