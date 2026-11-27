# core/service.py
# Single Core Engine Facade decoupling all UIs from hand-written data structures and SQLite.
# Course mapping: All DSA Sessions (Facade coordinating HashTable, Graph, Queues, Stacks, Heap, Trie, AVL).

import time
from typing import Callable

from core.auth import AccountManager, normalize_username
from core.communities import CommunityDetector
from core.connections import ConnectionManager
from core.ds.algorithms import merge_sort
from core.ds.avl_tree import AVLTree
from core.ds.hash_table import HashTable
from core.ds.stack import Stack
from core.engagement import EngagementManager
from core.feed import FeedEngine
from core.graph import SocialGraph
from core.models import (
    Comment,
    CommunityInfo,
    ConnectionRequest,
    DegreeResult,
    Notification,
    Post,
    Suggestion,
    TrendingPost,
    UndoAction,
    User,
    ValidationError,
)
from core.notifications import NotificationManager
from core.posts import PostManager
from core.search import UserSearchIndex
from core.suggestions import SuggestionEngine
from storage.repository import SQLiteRepository


class ScreenNavigator:
    """UI navigation history helper backed by our hand-written LIFO Stack.

    Exposed through `core.service` so interfaces (such as the console menu) can
    implement back-navigation without importing `core.ds` directly.
    """

    def __init__(self, initial_screen: str) -> None:
        """Initialize navigation history with an initial screen name.

        Time: O(1)
        Space: O(1)
        """
        self._history: Stack = Stack()
        self._history.push(initial_screen)

    def current(self) -> str:
        """Return the active screen at the top of the navigation stack.

        Time: O(1)
        Space: O(1)
        """
        return self._history.peek()

    def push(self, screen: str) -> None:
        """Navigate forward to `screen` by pushing it onto the stack.

        Time: O(1)
        Space: O(1)
        """
        self._history.push(screen)

    def back(self) -> str:
        """Pop the current screen and return the previous screen (stays at root if depth == 1).

        Time: O(1)
        Space: O(1)
        """
        if len(self._history) > 1:
            self._history.pop()
        return self._history.peek()

    def reset(self, screen: str) -> None:
        """Clear history and start fresh at `screen` (e.g. after login or logout).

        Time: O(1)
        Space: O(1)
        """
        self._history.clear()
        self._history.push(screen)

    def breadcrumb(self) -> str:
        """Return a readable `Home > Connections > Mutuals` trail from bottom to top.

        Time: O(D), where D is current navigation depth
        Space: O(D)
        """
        trail = self._history.to_list()
        trail.reverse()
        return " > ".join(trail)


class CUConnectService:
    """Unified facade over CUConnect's in-memory DSA engine and write-through SQLite storage.

    Architecture rule:
    - Both the console app (`ui/console_app.py`) and the Streamlit app (`ui/streamlit_app.py`)
      call ONLY methods on this class and never touch the underlying data structures or SQLite.
    - At startup, all persisted rows are loaded from SQLite into memory. Thereafter,
      all reads and graph algorithms execute strictly in memory, while every mutation
      writes through immediately to SQLite.
    """

    def __init__(
        self,
        db_path: str = "cuconnect.db",
        clock: Callable[[], float] | None = None,
    ) -> None:
        """Initialize the service, open SQLite storage, and hydrate all in-memory structures.

        Time: O(V log V + E + P log P + C log C + N log N) on startup hydration
        Space: O(V + E + P + C + N)
        """
        self._db_path = db_path
        self._clock: Callable[[], float] = clock if clock is not None else time.time
        self._seq: int = 0

        self._repo = SQLiteRepository(db_path)
        self._accounts = AccountManager()
        self._graph = SocialGraph()
        self._connections = ConnectionManager(self._graph)
        self._posts = PostManager()
        self._feed = FeedEngine(self._graph, self._posts)
        self._suggestions = SuggestionEngine(self._graph, self._accounts, self._connections)
        self._search = UserSearchIndex(self._accounts)
        self._notifications = NotificationManager()
        self._engagement = EngagementManager(self._graph, self._posts)
        self._communities = CommunityDetector(self._graph)
        self._directory = AVLTree()
        self._undo_stacks: HashTable = HashTable(initial_capacity=32)

        self._hydrate_from_storage()

    def _next_seq(self) -> int:
        """Return the next monotonically increasing sequence ID for deterministic tie-breaking."""
        self._seq += 1
        return self._seq

    def _now(self) -> float:
        """Return the current timestamp from the injectable clock."""
        return float(self._clock())

    def _directory_key(self, user: User) -> tuple[str, str]:
        """Alphabetical AVL sort key: case-insensitive full name, then username."""
        return (user.full_name.lower(), user.username)

    def _register_in_subsystems(self, user: User) -> None:
        """Attach a loaded or newly signed-up user to every in-memory subsystem."""
        self._graph.add_user(user.username)
        self._connections.register_user(user.username)
        self._posts.register_user(user.username)
        self._notifications.register_user(user.username)
        self._search.index_user(user)
        self._directory.insert(self._directory_key(user), user)
        self._undo_stacks.put(user.username, Stack())

    def _hydrate_from_storage(self) -> None:
        """Load all persisted records from SQLite into our hand-written in-memory structures."""
        max_seq = 0

        # 1. Users
        for user in self._repo.load_all_users():
            self._accounts.load_user(user)
            self._register_in_subsystems(user)

        # 2. Undirected connections
        for user_a, user_b in self._repo.load_all_connections():
            if self._graph.has_user(user_a) and self._graph.has_user(user_b):
                if not self._graph.has_edge(user_a, user_b):
                    self._graph.add_edge(user_a, user_b)

        # 3. Pending connection requests (sorted by seq_id in Python via merge_sort)
        requests = merge_sort(
            self._repo.load_all_requests(),
            key=lambda r: (r.seq_id, r.created_at),
        )
        for req in requests:
            self._connections.load_request(req)
            if req.seq_id > max_seq:
                max_seq = req.seq_id

        # 4. Posts (oldest first so prepending at SinglyLinkedList head leaves newest at head)
        posts = merge_sort(
            self._repo.load_all_posts(),
            key=lambda p: (p.created_at, p.seq_id),
        )
        for post in posts:
            self._posts.load_post(post)
            if post.seq_id > max_seq:
                max_seq = post.seq_id

        # 5. Likes
        for post_id, username, created_at in self._repo.load_all_likes():
            self._engagement.like_post(post_id, username, created_at)

        # 6. Comments (sorted by seq_id guarantees every parent comment loads before replies)
        comments = merge_sort(
            self._repo.load_all_comments(),
            key=lambda c: (c.seq_id, c.created_at),
        )
        for comment in comments:
            self._engagement.add_comment(
                post_id=comment.post_id,
                author=comment.author,
                content=comment.content,
                created_at=comment.created_at,
                seq_id=comment.seq_id,
                parent_comment_id=comment.parent_comment_id,
                comment_id=comment.comment_id,
            )
            if comment.seq_id > max_seq:
                max_seq = comment.seq_id

        # 7. Notifications
        notifications = merge_sort(
            self._repo.load_all_notifications(),
            key=lambda n: (n.seq_id, n.created_at),
        )
        for notif in notifications:
            self._notifications.load_notification(notif)
            if notif.seq_id > max_seq:
                max_seq = notif.seq_id

        self._seq = max_seq

    def close(self) -> None:
        """Close the SQLite repository cleanly.

        Time: O(1)
        Space: O(1)
        """
        self._repo.close()

    # =========================================================================
    # Part 1: Accounts & Profiles
    # =========================================================================

    def sign_up(
        self,
        username: str,
        password: str,
        full_name: str,
        programme: str,
        year: int,
        bio: str = "",
        skills: list[str] | None = None,
    ) -> User:
        """Register a new student account, index across all structures, and write through to DB.

        Time: O(log V + L_name) + PBKDF2 hashing cost
        Space: O(L_name)
        """
        now = self._now()
        user = self._accounts.register_user(
            username=username,
            password=password,
            full_name=full_name,
            programme=programme,
            year=year,
            bio=bio,
            skills=skills,
            created_at=now,
        )
        self._register_in_subsystems(user)
        self._repo.save_user(user)
        return user

    def login(self, username: str, password: str) -> User:
        """Authenticate a user and start their session.

        Time: O(1) average lookup + PBKDF2 verification cost
        Space: O(1)
        """
        return self._accounts.login(username, password)

    def logout(self, username: str) -> None:
        """Log out a user session.

        Time: O(1) average
        Space: O(1)
        """
        self._accounts.logout(username)

    def is_logged_in(self, username: str) -> bool:
        """Return True if `username` currently has an active login session.

        Time: O(1) average
        Space: O(1)
        """
        return self._accounts.is_logged_in(username)

    def get_profile(self, username: str) -> User:
        """Fetch a student's User profile by username.

        Time: O(1) average
        Space: O(1)
        """
        return self._accounts.get_user(username)

    def update_profile(
        self,
        username: str,
        full_name: str | None = None,
        programme: str | None = None,
        year: int | None = None,
        bio: str | None = None,
        skills: list[str] | None = None,
    ) -> User:
        """Edit profile fields, keep Trie & AVL directory synchronized, and write through to DB.

        Time: O(log V + L_old + L_new)
        Space: O(L_new + S)
        """
        existing = self._accounts.get_user(username)
        old_name = existing.full_name
        old_dir_key = self._directory_key(existing)

        updated = self._accounts.update_profile(
            username=username,
            full_name=full_name,
            programme=programme,
            year=year,
            bio=bio,
            skills=skills,
        )

        if updated.full_name != old_name:
            self._search.reindex_user(old_name, updated)
            self._directory.delete(old_dir_key)
            self._directory.insert(self._directory_key(updated), updated)

        self._repo.update_user(updated)
        return updated

    # =========================================================================
    # Part 2: Connections, Requests, Mutuals, BFS Degree/Chain, Suggestions
    # =========================================================================

    def _emit_notification(
        self,
        recipient: str,
        actor: str,
        kind: str,
        message: str,
        ref_id: str | None = None,
    ) -> Notification:
        """Enqueue a notification in memory and write through to SQLite."""
        notif = self._notifications.notify(
            recipient=recipient,
            actor=actor,
            kind=kind,
            message=message,
            created_at=self._now(),
            seq_id=self._next_seq(),
            ref_id=ref_id,
        )
        self._repo.save_notification(notif)
        return notif

    def send_connection_request(self, sender: str, receiver: str) -> str:
        """Send a connection request from `sender` to `receiver` (auto-accepts on reverse pending).

        Returns `"pending"` or `"auto_accepted"`.

        Time: O(deg(sender) + deg(receiver) + pending_count)
        Space: O(1)
        """
        s = normalize_username(sender)
        r = normalize_username(receiver)
        now = self._now()
        seq = self._next_seq()

        status, req = self._connections.send_request(s, r, now, seq)

        if status == "auto_accepted":
            self._repo.delete_request(r, s)
            self._repo.save_connection(s, r, now)
            sender_user = self._accounts.get_user(s)
            receiver_user = self._accounts.get_user(r)
            self._emit_notification(
                recipient=r,
                actor=s,
                kind="request_accepted",
                message=f"{sender_user.full_name} (@{s}) also requested to connect — you are now connected!",
                ref_id=s,
            )
            self._emit_notification(
                recipient=s,
                actor=r,
                kind="request_accepted",
                message=f"Mutual request with {receiver_user.full_name} (@{r}) was auto-accepted!",
                ref_id=r,
            )
        else:
            self._repo.save_request(req)
            sender_user = self._accounts.get_user(s)
            self._emit_notification(
                recipient=r,
                actor=s,
                kind="connection_request",
                message=f"{sender_user.full_name} (@{s}) sent you a connection request.",
                ref_id=s,
            )
            undo_stack: Stack = self._undo_stacks.get(s)
            undo_stack.push(UndoAction("send_request", s, r, now))

        return status

    def accept_connection_request(self, actor: str, sender: str) -> None:
        """Accept an incoming connection request from `sender` to `actor`.

        Time: O(deg(actor) + deg(sender) + pending_count)
        Space: O(1)
        """
        a = normalize_username(actor)
        s = normalize_username(sender)
        self._connections.accept_request(a, s)
        now = self._now()
        self._repo.delete_request(s, a)
        self._repo.save_connection(s, a, now)

        actor_user = self._accounts.get_user(a)
        self._emit_notification(
            recipient=s,
            actor=a,
            kind="request_accepted",
            message=f"{actor_user.full_name} (@{a}) accepted your connection request.",
            ref_id=a,
        )

    def reject_connection_request(self, actor: str, sender: str) -> None:
        """Reject an incoming connection request from `sender` to `actor`.

        Time: O(pending_count)
        Space: O(1)
        """
        a = normalize_username(actor)
        s = normalize_username(sender)
        self._connections.reject_request(a, s)
        self._repo.delete_request(s, a)

    def cancel_connection_request(self, actor: str, receiver: str) -> None:
        """Cancel an outgoing connection request sent by `actor` to `receiver`.

        Time: O(pending_count)
        Space: O(1)
        """
        a = normalize_username(actor)
        r = normalize_username(receiver)
        self._connections.cancel_request(a, r)
        self._repo.delete_request(a, r)

    def remove_connection(self, actor: str, target: str) -> None:
        """Remove an existing accepted connection between `actor` and `target` in both directions.

        Time: O(deg(actor) + deg(target))
        Space: O(1)
        """
        a = normalize_username(actor)
        t = normalize_username(target)
        self._connections.remove_connection(a, t)
        self._repo.delete_connection(a, t)

        undo_stack: Stack = self._undo_stacks.get(a)
        undo_stack.push(UndoAction("remove_connection", a, t, self._now()))

    def undo_last_action(self, username: str) -> str:
        """Undo the most recent reversible connection action (`send_request` or `remove_connection`).

        Uses our hand-written LIFO Stack per user and writes through to SQLite.

        Time: O(deg(actor) + deg(target) + pending_count)
        Space: O(1)
        """
        uname = normalize_username(username)
        self._accounts.get_user(uname)
        undo_stack: Stack = self._undo_stacks.get(uname)
        if undo_stack.is_empty():
            raise ValidationError("Nothing to undo.")

        action: UndoAction = undo_stack.pop()

        if action.action_type == "send_request":
            if not self._connections.has_pending_request(action.actor, action.target):
                raise ValidationError(
                    f"Cannot undo request to @{action.target}: it is no longer pending."
                )
            self._connections.cancel_request(action.actor, action.target)
            self._repo.delete_request(action.actor, action.target)
            return f"Undid connection request to @{action.target}."

        if action.action_type == "remove_connection":
            if self._graph.has_edge(action.actor, action.target):
                raise ValidationError(
                    f"Cannot undo removal: you are already connected with @{action.target}."
                )
            # Clear any intermediate pending request so graph invariants stay clean.
            if self._connections.has_pending_request(action.actor, action.target):
                self._connections.cancel_request(action.actor, action.target)
                self._repo.delete_request(action.actor, action.target)
            if self._connections.has_pending_request(action.target, action.actor):
                self._connections.reject_request(action.actor, action.target)
                self._repo.delete_request(action.target, action.actor)

            self._graph.add_edge(action.actor, action.target)
            self._repo.save_connection(action.actor, action.target, self._now())
            return f"Restored connection with @{action.target}."

        raise ValidationError(f"Unsupported undo action: {action.action_type}")

    def can_undo(self, username: str) -> bool:
        """Return True if `username` has at least one action on their undo Stack.

        Time: O(1) average
        Space: O(1)
        """
        uname = normalize_username(username)
        self._accounts.get_user(uname)
        undo_stack: Stack = self._undo_stacks.get(uname)
        return not undo_stack.is_empty()

    def get_connections(self, username: str) -> list[User]:
        """Return alphabetically sorted User profiles connected to `username`.

        Time: O(deg(username))
        Space: O(deg(username))
        """
        uname = normalize_username(username)
        neighbor_names = self._graph.neighbors(uname)
        return [self._accounts.get_user(n) for n in neighbor_names]

    def get_connection_usernames(self, username: str) -> list[str]:
        """Return alphabetically sorted usernames connected to `username`.

        Time: O(deg(username))
        Space: O(deg(username))
        """
        return self._graph.neighbors(normalize_username(username))

    def get_incoming_requests(self, username: str) -> list[ConnectionRequest]:
        """Return pending incoming connection requests in FIFO arrival order.

        Time: O(pending_in)
        Space: O(pending_in)
        """
        return self._connections.incoming_requests(normalize_username(username))

    def get_outgoing_requests(self, username: str) -> list[ConnectionRequest]:
        """Return pending outgoing connection requests in FIFO arrival order.

        Time: O(pending_out)
        Space: O(pending_out)
        """
        return self._connections.outgoing_requests(normalize_username(username))

    def get_mutual_connections(self, user_a: str, user_b: str) -> list[User]:
        """Return sorted mutual connection User profiles shared by `user_a` and `user_b`.

        Time: O(deg(user_a) + deg(user_b))
        Space: O(min(deg(user_a), deg(user_b)))
        """
        a = normalize_username(user_a)
        b = normalize_username(user_b)
        mutual_names = self._graph.mutual_connections(a, b)
        return [self._accounts.get_user(m) for m in mutual_names]

    def get_degree_and_chain(self, source: str, target: str) -> DegreeResult:
        """Compute degree of connection (1st/2nd/3rd/3+) and shortest path via BFS.

        Time: O(V + E)
        Space: O(V)
        """
        return self._graph.degree_and_shortest_path(
            normalize_username(source),
            normalize_username(target),
        )

    def get_people_you_may_know(self, username: str, k: int = 5) -> list[Suggestion]:
        """Return top-`k` 'People You May Know' suggestions via Depth-2 BFS + Jaccard + MinHeap.

        Time: O(sum_{w in N(u)} deg(w) + C * (deg(u) + deg(c)) + C log C)
        Space: O(deg(u) + C)
        """
        return self._suggestions.recommend(normalize_username(username), k=k)

    # =========================================================================
    # Part 3: Posts & Home Feed
    # =========================================================================

    def create_post(self, author: str, content: str, image_path: str | None = None) -> Post:
        """Create a post (optionally with an image) at the head of `author`'s SinglyLinkedList and persist it.

        Time: O(1) average
        Space: O(1)
        """
        uname = normalize_username(author)
        post = self._posts.create_post(
            author=uname,
            content=content,
            created_at=self._now(),
            seq_id=self._next_seq(),
            image_path=image_path,
        )
        self._repo.save_post(post)
        return post

    def get_user_posts(self, username: str) -> list[Post]:
        """Return all posts authored by `username`, newest first.

        Time: O(P_u)
        Space: O(P_u)
        """
        return self._posts.get_user_posts(normalize_username(username))

    def delete_post(self, actor: str, post_id: str) -> Post:
        """Delete `post_id` (only allowed by its author) along with its likes and comments.

        Time: O(P_author + C_post)
        Space: O(H_comments)
        """
        uname = normalize_username(actor)
        deleted = self._posts.delete_post(uname, post_id)
        self._engagement.remove_post_engagement(post_id)
        self._repo.delete_post(post_id)
        return deleted

    def get_home_feed(
        self,
        username: str,
        limit: int = 10,
        offset: int = 0,
        include_self: bool = False,
    ) -> tuple[list[Post], bool]:
        """Build a paginated newest-first home feed via k-way MinHeap merge.

        Time: O((k + offset + limit) log k)
        Space: O(k + limit)
        """
        return self._feed.get_home_feed(
            normalize_username(username),
            limit=limit,
            offset=offset,
            include_self=include_self,
        )

    # =========================================================================
    # Part 4: Prefix Search (Trie)
    # =========================================================================

    def search_users(self, prefix: str, limit: int = 10) -> list[User]:
        """Return up to `limit` users whose username or name words start with `prefix`.

        Time: O(L + M + U log U)
        Space: O(M + U)
        """
        return self._search.search(prefix, limit=limit)

    # =========================================================================
    # Enhancements: Notifications, Likes, Threaded Comments, Trending, Communities, AVL Browse
    # =========================================================================

    def get_notifications(self, username: str, unread_only: bool = False) -> list[Notification]:
        """Return notifications from `username`'s Notification Queue.

        Time: O(N_u)
        Space: O(N_u)
        """
        return self._notifications.get_notifications(
            normalize_username(username),
            unread_only=unread_only,
        )

    def get_unread_notification_count(self, username: str) -> int:
        """Return the number of unread notifications for `username`.

        Time: O(N_u)
        Space: O(1)
        """
        return self._notifications.unread_count(normalize_username(username))

    def mark_notification_read(self, username: str, notification_id: str) -> Notification:
        """Mark one notification as read in memory and SQLite.

        Time: O(1) average
        Space: O(1)
        """
        notif = self._notifications.mark_read(normalize_username(username), notification_id)
        self._repo.mark_notification_read(notification_id)
        return notif

    def mark_all_notifications_read(self, username: str) -> int:
        """Mark all unread notifications for `username` as read and return count updated.

        Time: O(N_u)
        Space: O(N_u)
        """
        marked_ids = self._notifications.mark_all_read(normalize_username(username))
        for nid in marked_ids:
            self._repo.mark_notification_read(nid)
        return len(marked_ids)

    def like_post(self, post_id: str, username: str) -> bool:
        """Like a post (stored in per-post HashTable), notify author, and write through.

        Time: O(1) average
        Space: O(1)
        """
        uname = normalize_username(username)
        liker = self._accounts.get_user(uname)
        post = self._posts.get_post(post_id)
        now = self._now()

        added = self._engagement.like_post(post_id, uname, now)
        if added:
            self._repo.save_like(post_id, uname, now)
            if post.author != uname:
                self._emit_notification(
                    recipient=post.author,
                    actor=uname,
                    kind="post_like",
                    message=f"{liker.full_name} (@{uname}) liked your post.",
                    ref_id=post_id,
                )
        return added

    def unlike_post(self, post_id: str, username: str) -> bool:
        """Remove `username`'s like from `post_id` and write through to SQLite.

        Time: O(1) average
        Space: O(1)
        """
        uname = normalize_username(username)
        self._accounts.get_user(uname)
        removed = self._engagement.unlike_post(post_id, uname)
        if removed:
            self._repo.delete_like(post_id, uname)
        return removed

    def toggle_like(self, post_id: str, username: str) -> bool:
        """Toggle like state on `post_id`; returns True if now liked, False if unliked.

        Time: O(1) average
        Space: O(1)
        """
        uname = normalize_username(username)
        if self._engagement.has_liked(post_id, uname):
            self.unlike_post(post_id, uname)
            return False
        self.like_post(post_id, uname)
        return True

    def has_liked(self, post_id: str, username: str) -> bool:
        """Return True if `username` has liked `post_id`.

        Time: O(1) average
        Space: O(1)
        """
        return self._engagement.has_liked(post_id, normalize_username(username))

    def get_like_count(self, post_id: str) -> int:
        """Return the number of likes on `post_id`.

        Time: O(1) average
        Space: O(1)
        """
        return self._engagement.like_count(post_id)

    def get_likers(self, post_id: str) -> list[str]:
        """Return alphabetically sorted usernames who liked `post_id`.

        Time: O(L log L)
        Space: O(L)
        """
        return self._engagement.get_likers(post_id)

    def add_comment(
        self,
        post_id: str,
        author: str,
        content: str,
        parent_comment_id: str | None = None,
    ) -> Comment:
        """Add a top-level comment or threaded reply, persist, and notify relevant authors.

        Time: O(1) average
        Space: O(1)
        """
        uname = normalize_username(author)
        commenter = self._accounts.get_user(uname)
        post = self._posts.get_post(post_id)
        now = self._now()
        seq = self._next_seq()

        comment = self._engagement.add_comment(
            post_id=post_id,
            author=uname,
            content=content,
            created_at=now,
            seq_id=seq,
            parent_comment_id=parent_comment_id,
        )
        self._repo.save_comment(comment)

        notified: set[str] = {uname}
        if parent_comment_id is not None:
            parent_comment = self._engagement.get_comment(parent_comment_id)
            if parent_comment.author not in notified:
                self._emit_notification(
                    recipient=parent_comment.author,
                    actor=uname,
                    kind="comment_reply",
                    message=f"{commenter.full_name} (@{uname}) replied to your comment.",
                    ref_id=post_id,
                )
                notified.add(parent_comment.author)

        if post.author not in notified:
            self._emit_notification(
                recipient=post.author,
                actor=uname,
                kind="post_comment",
                message=f"{commenter.full_name} (@{uname}) commented on your post.",
                ref_id=post_id,
            )

        return comment

    def get_post_comments(self, post_id: str) -> list[tuple[Comment, int]]:
        """Return `(Comment, depth)` pairs for `post_id` via pre-order DFS.

        Time: O(C)
        Space: O(C)
        """
        return self._engagement.get_comments_preorder(post_id)

    def get_comment_count(self, post_id: str) -> int:
        """Return total comments + nested replies on `post_id`.

        Time: O(C)
        Space: O(H)
        """
        return self._engagement.comment_count(post_id)

    def get_trending_posts(
        self,
        username: str,
        k: int = 5,
        window_seconds: float = 7 * 86400.0,
    ) -> list[TrendingPost]:
        """Return top-`k` recent trending posts among `username`'s connections using MinHeap.

        Time: O(R log R)
        Space: O(R)
        """
        return self._engagement.get_trending_posts(
            username=normalize_username(username),
            now=self._now(),
            k=k,
            window_seconds=window_seconds,
        )

    def get_all_communities(self) -> list[CommunityInfo]:
        """Return all connected-component communities found via iterative DFS + Stack.

        Time: O(V log V + E)
        Space: O(V)
        """
        return self._communities.find_all_communities()

    def get_user_community(self, username: str) -> CommunityInfo:
        """Return the CommunityInfo containing `username` (members and size).

        Time: O(V log V + E)
        Space: O(V)
        """
        return self._communities.get_user_community(normalize_username(username))

    def browse_all_students(self) -> list[User]:
        """Return all registered students in alphabetical order via AVL Tree in-order traversal.

        Time: O(V)
        Space: O(V)
        """
        return self._directory.inorder()

    def get_engine_stats(self) -> dict[str, object]:
        """Return diagnostic metrics about the live in-memory data structures for viva demos.

        Time: O(V log V + E)
        Space: O(V)
        """
        return {
            "users": self._accounts.count(),
            "connections": self._graph.edge_count(),
            "posts": self._posts.total_posts(),
            "hash_table_load_factor": round(self._accounts.hash_table_load_factor(), 3),
            "avl_height": self._directory.height(),
            "avl_balanced": self._directory.is_balanced(),
            "communities": len(self._communities.find_all_communities()),
        }
