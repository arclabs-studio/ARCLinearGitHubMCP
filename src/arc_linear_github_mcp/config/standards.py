"""ARC Labs Studio naming standards and conventions."""

from enum import Enum
from typing import Final


class BranchType(str, Enum):
    """Valid branch types for ARC Labs naming convention."""

    FEATURE = "feature"
    BUGFIX = "bugfix"
    HOTFIX = "hotfix"
    DOCS = "docs"
    SPIKE = "spike"
    RELEASE = "release"


class CommitType(str, Enum):
    """Valid commit types following Conventional Commits."""

    FEAT = "feat"
    FIX = "fix"
    DOCS = "docs"
    STYLE = "style"
    REFACTOR = "refactor"
    PERF = "perf"
    TEST = "test"
    CHORE = "chore"
    BUILD = "build"
    CI = "ci"
    REVERT = "revert"


# Branch naming constants
BRANCH_TYPES: Final[frozenset[str]] = frozenset(t.value for t in BranchType)

# Commit type constants
COMMIT_TYPES: Final[frozenset[str]] = frozenset(t.value for t in CommitType)

# Regex patterns for validation
BRANCH_PATTERN: Final[str] = (
    r"^(feature|bugfix|hotfix|docs|spike|release)/"
    r"(?:([A-Z]+-\d+)-)?([a-z0-9]+(?:-[a-z0-9]+)*)$"
)

COMMIT_PATTERN: Final[str] = (
    r"^(feat|fix|docs|style|refactor|perf|test|chore|build|ci|revert)"
    r"(?:\(([a-z0-9-]+)\))?:\s+(.+)$"
)

# Issue ID pattern (e.g., FAVRES-123)
ISSUE_ID_PATTERN: Final[str] = r"^[A-Z]+-\d+$"

# PR title patterns
PR_TITLE_PATTERN: Final[str] = (
    r"^(Feature|Bugfix|Hotfix|Docs|Spike|Release)/([A-Z]+-\d+):\s+(.+)$"
)

# Branch type to PR title prefix mapping
BRANCH_TO_PR_PREFIX: Final[dict[str, str]] = {
    "feature": "Feature",
    "bugfix": "Bugfix",
    "hotfix": "Hotfix",
    "docs": "Docs",
    "spike": "Spike",
    "release": "Release",
}

# Commit type descriptions for documentation
COMMIT_TYPE_DESCRIPTIONS: Final[dict[str, str]] = {
    "feat": "A new feature",
    "fix": "A bug fix",
    "docs": "Documentation only changes",
    "style": "Changes that do not affect the meaning of the code",
    "refactor": "A code change that neither fixes a bug nor adds a feature",
    "perf": "A code change that improves performance",
    "test": "Adding missing tests or correcting existing tests",
    "chore": "Other changes that don't modify src or test files",
    "build": "Changes that affect the build system or external dependencies",
    "ci": "Changes to CI configuration files and scripts",
    "revert": "Reverts a previous commit",
}

# Linear priority levels
LINEAR_PRIORITY_LEVELS: Final[dict[int, str]] = {
    0: "No priority",
    1: "Urgent",
    2: "High",
    3: "Normal",
    4: "Low",
}

# Default Linear issue states
LINEAR_STATES: Final[list[str]] = [
    "Backlog",
    "Todo",
    "In Progress",
    "In Review",
    "Done",
    "Canceled",
]
