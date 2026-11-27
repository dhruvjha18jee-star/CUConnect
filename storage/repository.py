# storage/repository.py
# Storage-only SQLite repository with write-through CRUD (no graph queries in SQL).
# Course mapping: Persistence Layer (Part 5: Storage keeps data only; DSA runs in memory).

import json
import sqlite3

from core.models import Comment, ConnectionRequest, Notification, Post, User


class SQLiteRepository:
    """Thin SQLite storage layer performing strictly simple table CRUD.

    Design rule:
    - Every SQL statement is a plain SELECT *, INSERT, UPDATE, or DELETE.
    - No JOINs, recursive CTEs, aggregations, or sorting for graph/feed logic
      ever run inside SQLite; all data structures and algorithms execute in Python.
    """

    def __init__(self, db_path: str = "cuconnect.db") -> None:
        """Open (or create) the SQLite database file and initialize all tables.

        Time: O(1)
        Space: O(1)
        """
        self._db_path = db_path
        # check_same_thread=False allows Streamlit reruns to reuse the service safely.
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._create_tables()

    def _create_tables(self) -> None:
        """Create normalized storage tables if they do not already exist."""
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    programme TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    bio TEXT NOT NULL,
                    skills TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS connections (
                    user_a TEXT NOT NULL,
                    user_b TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    PRIMARY KEY (user_a, user_b)
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS connection_requests (
                    sender TEXT NOT NULL,
                    receiver TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    seq_id INTEGER NOT NULL,
                    PRIMARY KEY (sender, receiver)
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS posts (
                    post_id TEXT PRIMARY KEY,
                    author TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    seq_id INTEGER NOT NULL,
                    image_path TEXT
                )
                """
            )
            post_cols = {
                row["name"]
                for row in self._conn.execute("PRAGMA table_info(posts)").fetchall()
            }
            if "image_path" not in post_cols:
                self._conn.execute("ALTER TABLE posts ADD COLUMN image_path TEXT")
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS post_likes (
                    post_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    PRIMARY KEY (post_id, username)
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS comments (
                    comment_id TEXT PRIMARY KEY,
                    post_id TEXT NOT NULL,
                    author TEXT NOT NULL,
                    parent_comment_id TEXT,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    seq_id INTEGER NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id TEXT PRIMARY KEY,
                    recipient TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    message TEXT NOT NULL,
                    ref_id TEXT,
                    created_at REAL NOT NULL,
                    seq_id INTEGER NOT NULL,
                    is_read INTEGER NOT NULL DEFAULT 0
                )
                """
            )

    def close(self) -> None:
        """Close the underlying SQLite connection cleanly.

        Time: O(1)
        Space: O(1)
        """
        self._conn.close()

    # --- Users ---

    def save_user(self, user: User) -> None:
        """Insert a new User row into SQLite.

        Time: O(1)
        Space: O(1)
        """
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO users (
                    username, password_hash, full_name, programme,
                    year, bio, skills, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.username,
                    user.password_hash,
                    user.full_name,
                    user.programme,
                    user.year,
                    user.bio,
                    json.dumps(user.skills),
                    user.created_at,
                ),
            )

    def update_user(self, user: User) -> None:
        """Persist updated profile fields for an existing User.

        Time: O(1)
        Space: O(1)
        """
        with self._conn:
            self._conn.execute(
                """
                UPDATE users
                SET full_name = ?, programme = ?, year = ?, bio = ?, skills = ?
                WHERE username = ?
                """,
                (
                    user.full_name,
                    user.programme,
                    user.year,
                    user.bio,
                    json.dumps(user.skills),
                    user.username,
                ),
            )

    def load_all_users(self) -> list[User]:
        """Load every User row for startup hydration into memory.

        Time: O(V)
        Space: O(V)
        """
        rows = self._conn.execute("SELECT * FROM users").fetchall()
        users: list[User] = []
        for row in rows:
            users.append(
                User(
                    username=row["username"],
                    password_hash=row["password_hash"],
                    full_name=row["full_name"],
                    programme=row["programme"],
                    year=int(row["year"]),
                    bio=row["bio"],
                    skills=json.loads(row["skills"]),
                    created_at=float(row["created_at"]),
                )
            )
        return users

    # --- Accepted Connections (Undirected Edges) ---

    def _canonical_pair(self, user_a: str, user_b: str) -> tuple[str, str]:
        """Store undirected edges canonically with smaller username first."""
        return (user_a, user_b) if user_a < user_b else (user_b, user_a)

    def save_connection(self, user_a: str, user_b: str, created_at: float) -> None:
        """Persist an accepted undirected connection edge.

        Time: O(1)
        Space: O(1)
        """
        first, second = self._canonical_pair(user_a, user_b)
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO connections (user_a, user_b, created_at) VALUES (?, ?, ?)",
                (first, second, created_at),
            )

    def delete_connection(self, user_a: str, user_b: str) -> None:
        """Delete an accepted undirected connection edge.

        Time: O(1)
        Space: O(1)
        """
        first, second = self._canonical_pair(user_a, user_b)
        with self._conn:
            self._conn.execute(
                "DELETE FROM connections WHERE user_a = ? AND user_b = ?",
                (first, second),
            )

    def load_all_connections(self) -> list[tuple[str, str]]:
        """Load all accepted undirected edges for startup graph construction.

        Time: O(E)
        Space: O(E)
        """
        rows = self._conn.execute("SELECT user_a, user_b FROM connections").fetchall()
        return [(row["user_a"], row["user_b"]) for row in rows]

    # --- Pending Connection Requests (Directed Edges) ---

    def save_request(self, req: ConnectionRequest) -> None:
        """Persist a directed pending connection request.

        Time: O(1)
        Space: O(1)
        """
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO connection_requests (sender, receiver, created_at, seq_id)
                VALUES (?, ?, ?, ?)
                """,
                (req.sender, req.receiver, req.created_at, req.seq_id),
            )

    def delete_request(self, sender: str, receiver: str) -> None:
        """Delete a directed pending connection request.

        Time: O(1)
        Space: O(1)
        """
        with self._conn:
            self._conn.execute(
                "DELETE FROM connection_requests WHERE sender = ? AND receiver = ?",
                (sender, receiver),
            )

    def load_all_requests(self) -> list[ConnectionRequest]:
        """Load all pending directed requests for startup queue hydration.

        Time: O(R), where R is the number of pending requests
        Space: O(R)
        """
        rows = self._conn.execute("SELECT * FROM connection_requests").fetchall()
        return [
            ConnectionRequest(
                sender=row["sender"],
                receiver=row["receiver"],
                created_at=float(row["created_at"]),
                seq_id=int(row["seq_id"]),
            )
            for row in rows
        ]

    # --- Posts ---

    def save_post(self, post: Post) -> None:
        """Persist a newly created post (with optional image path).

        Time: O(1)
        Space: O(1)
        """
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO posts (post_id, author, content, created_at, seq_id, image_path)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    post.post_id,
                    post.author,
                    post.content,
                    post.created_at,
                    post.seq_id,
                    post.image_path,
                ),
            )

    def delete_post(self, post_id: str) -> None:
        """Delete a post along with its persisted likes and comments.

        Time: O(1)
        Space: O(1)
        """
        with self._conn:
            self._conn.execute("DELETE FROM post_likes WHERE post_id = ?", (post_id,))
            self._conn.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
            self._conn.execute("DELETE FROM posts WHERE post_id = ?", (post_id,))

    def load_all_posts(self) -> list[Post]:
        """Load all persisted posts for startup linked-list hydration.

        Time: O(P)
        Space: O(P)
        """
        rows = self._conn.execute("SELECT * FROM posts").fetchall()
        return [
            Post(
                post_id=row["post_id"],
                author=row["author"],
                content=row["content"],
                created_at=float(row["created_at"]),
                seq_id=int(row["seq_id"]),
                image_path=row["image_path"],
            )
            for row in rows
        ]

    # --- Post Likes ---

    def save_like(self, post_id: str, username: str, created_at: float) -> None:
        """Persist a post like.

        Time: O(1)
        Space: O(1)
        """
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO post_likes (post_id, username, created_at) VALUES (?, ?, ?)",
                (post_id, username, created_at),
            )

    def delete_like(self, post_id: str, username: str) -> None:
        """Delete a persisted post like.

        Time: O(1)
        Space: O(1)
        """
        with self._conn:
            self._conn.execute(
                "DELETE FROM post_likes WHERE post_id = ? AND username = ?",
                (post_id, username),
            )

    def load_all_likes(self) -> list[tuple[str, str, float]]:
        """Load all persisted likes as `(post_id, username, created_at)`.

        Time: O(L)
        Space: O(L)
        """
        rows = self._conn.execute("SELECT post_id, username, created_at FROM post_likes").fetchall()
        return [(row["post_id"], row["username"], float(row["created_at"])) for row in rows]

    # --- Comments ---

    def save_comment(self, comment: Comment) -> None:
        """Persist a top-level comment or reply node.

        Time: O(1)
        Space: O(1)
        """
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO comments (
                    comment_id, post_id, author, parent_comment_id,
                    content, created_at, seq_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    comment.comment_id,
                    comment.post_id,
                    comment.author,
                    comment.parent_comment_id,
                    comment.content,
                    comment.created_at,
                    comment.seq_id,
                ),
            )

    def load_all_comments(self) -> list[Comment]:
        """Load all persisted comments for startup comment-tree reconstruction.

        Time: O(C)
        Space: O(C)
        """
        rows = self._conn.execute("SELECT * FROM comments").fetchall()
        return [
            Comment(
                comment_id=row["comment_id"],
                post_id=row["post_id"],
                author=row["author"],
                parent_comment_id=row["parent_comment_id"],
                content=row["content"],
                created_at=float(row["created_at"]),
                seq_id=int(row["seq_id"]),
            )
            for row in rows
        ]

    # --- Notifications ---

    def save_notification(self, notif: Notification) -> None:
        """Persist a new notification row.

        Time: O(1)
        Space: O(1)
        """
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO notifications (
                    notification_id, recipient, actor, kind, message,
                    ref_id, created_at, seq_id, is_read
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    notif.notification_id,
                    notif.recipient,
                    notif.actor,
                    notif.kind,
                    notif.message,
                    notif.ref_id,
                    notif.created_at,
                    notif.seq_id,
                    1 if notif.is_read else 0,
                ),
            )

    def mark_notification_read(self, notification_id: str) -> None:
        """Persist read status for one notification.

        Time: O(1)
        Space: O(1)
        """
        with self._conn:
            self._conn.execute(
                "UPDATE notifications SET is_read = 1 WHERE notification_id = ?",
                (notification_id,),
            )

    def load_all_notifications(self) -> list[Notification]:
        """Load all persisted notifications for startup queue hydration.

        Time: O(N)
        Space: O(N)
        """
        rows = self._conn.execute("SELECT * FROM notifications").fetchall()
        return [
            Notification(
                notification_id=row["notification_id"],
                recipient=row["recipient"],
                actor=row["actor"],
                kind=row["kind"],
                message=row["message"],
                ref_id=row["ref_id"],
                created_at=float(row["created_at"]),
                seq_id=int(row["seq_id"]),
                is_read=bool(row["is_read"]),
            )
            for row in rows
        ]
