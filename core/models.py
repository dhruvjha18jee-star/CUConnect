# core/models.py
# Domain data models (dataclasses) and explicit exception hierarchy for CUConnect.
# Course mapping: Session 1: Programming Prerequisites & Session 2: DSA Foundations.

from dataclasses import dataclass, field


class CUConnectError(Exception):
    """Base exception for all CUConnect core engine errors."""


class AuthError(CUConnectError):
    """Raised when login credentials are invalid or a session check fails."""


class UserNotFoundError(CUConnectError):
    """Raised when an operation references a username that does not exist."""


class ValidationError(CUConnectError):
    """Raised when user input fails validation rules (e.g. empty post, self-request)."""


class ConnectionRuleError(CUConnectError):
    """Raised when a connection or request violates graph/workflow invariants."""


class AuthorizationError(CUConnectError):
    """Raised when a user tries to perform an action only another user is allowed to do."""


class ResourceNotFoundError(CUConnectError):
    """Raised when a requested post, comment, request, or notification does not exist."""


@dataclass
class User:
    """Represents a student account and public profile on CUConnect."""

    username: str
    password_hash: str
    full_name: str
    programme: str
    year: int
    bio: str = ""
    skills: list[str] = field(default_factory=list)
    created_at: float = 0.0

    def public_profile(self) -> dict[str, object]:
        """Return a safe dictionary of profile fields without password_hash.

        Time: O(S), where S is the number of skills
        Space: O(S)
        """
        return {
            "username": self.username,
            "full_name": self.full_name,
            "programme": self.programme,
            "year": self.year,
            "bio": self.bio,
            "skills": list(self.skills),
            "created_at": self.created_at,
        }


@dataclass
class ConnectionRequest:
    """Directed pending edge from `sender` to `receiver` awaiting a response."""

    sender: str
    receiver: str
    created_at: float
    seq_id: int

    def __eq__(self, other: object) -> bool:
        """Compare requests by their directed endpoints (sender, receiver).

        Time: O(1)
        Space: O(1)
        """
        if not isinstance(other, ConnectionRequest):
            return False
        return self.sender == other.sender and self.receiver == other.receiver


@dataclass
class DegreeResult:
    """Result of a BFS degree-of-connection and shortest-chain query."""

    source: str
    target: str
    distance: int | None
    label: str
    path: list[str]


@dataclass
class Suggestion:
    """One ranked 'People You May Know' recommendation."""

    username: str
    full_name: str
    programme: str
    year: int
    jaccard_score: float
    mutual_count: int
    mutual_usernames: list[str]


@dataclass
class Post:
    """A post authored by a student about a project or technical idea (with optional image)."""

    post_id: str
    author: str
    content: str
    created_at: float
    seq_id: int
    image_path: str | None = None


@dataclass
class Comment:
    """A node in a post's comment tree; replies are stored as child Comment nodes."""

    comment_id: str
    post_id: str
    author: str
    parent_comment_id: str | None
    content: str
    created_at: float
    seq_id: int
    replies: list["Comment"] = field(default_factory=list)


@dataclass
class Notification:
    """A queued alert delivered to a user for social or engagement activity."""

    notification_id: str
    recipient: str
    actor: str
    kind: str
    message: str
    ref_id: str | None
    created_at: float
    seq_id: int
    is_read: bool = False


@dataclass
class TrendingPost:
    """A recent connection post ranked by engagement score = likes + 2 * comments."""

    post: Post
    like_count: int
    comment_count: int
    score: int


@dataclass
class CommunityInfo:
    """One connected component (student community) discovered by iterative DFS."""

    community_id: int
    members: list[str]
    size: int


@dataclass
class UndoAction:
    """Record pushed onto a user's undo Stack for reversible connection actions."""

    action_type: str  # "send_request" or "remove_connection"
    actor: str
    target: str
    created_at: float
