# core/engagement.py
# Post likes (per-post HashTable), threaded comment trees (pre-order DFS), and trending posts (MinHeap).
# Course mapping: Session 8: Trees (Pre-Order DFS) & Session 15: Heaps and Hash Tables.

import uuid

from core.ds.algorithms import merge_sort
from core.ds.hash_table import HashTable
from core.ds.heap import MinHeap
from core.graph import SocialGraph
from core.models import (
    Comment,
    ResourceNotFoundError,
    TrendingPost,
    ValidationError,
)
from core.posts import PostManager


class EngagementManager:
    """Manages post likes, nested comment trees, and trending post ranking.

    Data structures used:
    - Likes: `HashTable` mapping `post_id -> HashTable(username -> timestamp)` so
      checking or toggling a like is O(1) average and duplicate likes are impossible.
    - Comments: Each post owns a forest of `Comment` tree roots where every Comment
      holds a list of child `replies`. Rendering a thread runs pre-order DFS so
      every reply appears directly beneath its parent with exact nesting depth.
    - Trending posts: Scores recent posts from a user's connections as
      `likes + 2 * total_comments` and selects top-k via `MinHeap`.
    """

    MAX_COMMENT_LENGTH = 1000

    def __init__(self, graph: SocialGraph, posts: PostManager) -> None:
        """Initialize like tables and comment trees bound to graph and post managers.

        Time: O(1)
        Space: O(1)
        """
        self._graph = graph
        self._posts = posts
        self._likes_by_post: HashTable = HashTable(initial_capacity=64)
        self._root_comments_by_post: HashTable = HashTable(initial_capacity=64)
        self._comments_by_id: HashTable = HashTable(initial_capacity=64)

    def _get_or_create_like_table(self, post_id: str) -> HashTable:
        """Return the per-post like HashTable, allocating one if needed."""
        table: HashTable | None = self._likes_by_post.get(post_id)
        if table is None:
            table = HashTable(initial_capacity=8)
            self._likes_by_post.put(post_id, table)
        return table

    def _get_or_create_root_comments(self, post_id: str) -> list[Comment]:
        """Return the list of top-level comments for a post."""
        roots: list[Comment] | None = self._root_comments_by_post.get(post_id)
        if roots is None:
            roots = []
            self._root_comments_by_post.put(post_id, roots)
        return roots

    def like_post(self, post_id: str, username: str, created_at: float) -> bool:
        """Record a like from `username` on `post_id`. Returns True if newly liked.

        Time: O(1) average
        Space: O(1)
        """
        self._posts.get_post(post_id)
        like_table = self._get_or_create_like_table(post_id)
        if like_table.contains(username):
            return False
        like_table.put(username, created_at)
        return True

    def unlike_post(self, post_id: str, username: str) -> bool:
        """Remove `username`'s like from `post_id`. Returns True if previously liked.

        Time: O(1) average
        Space: O(1)
        """
        self._posts.get_post(post_id)
        like_table: HashTable | None = self._likes_by_post.get(post_id)
        if like_table is None or not like_table.contains(username):
            return False
        like_table.remove(username)
        return True

    def has_liked(self, post_id: str, username: str) -> bool:
        """Return True if `username` has liked `post_id`.

        Time: O(1) average
        Space: O(1)
        """
        like_table: HashTable | None = self._likes_by_post.get(post_id)
        if like_table is None:
            return False
        return like_table.contains(username)

    def like_count(self, post_id: str) -> int:
        """Return the total number of likes on `post_id`.

        Time: O(1) average
        Space: O(1)
        """
        like_table: HashTable | None = self._likes_by_post.get(post_id)
        return len(like_table) if like_table is not None else 0

    def get_likers(self, post_id: str) -> list[str]:
        """Return alphabetically sorted usernames who liked `post_id`.

        Time: O(L log L), where L is the number of likes on `post_id`
        Space: O(L)
        """
        self._posts.get_post(post_id)
        like_table: HashTable | None = self._likes_by_post.get(post_id)
        if like_table is None:
            return []
        return merge_sort(like_table.keys())

    def add_comment(
        self,
        post_id: str,
        author: str,
        content: str,
        created_at: float,
        seq_id: int,
        parent_comment_id: str | None = None,
        comment_id: str | None = None,
    ) -> Comment:
        """Add a top-level comment or reply node to a post's comment tree.

        Time: O(1) average
        Space: O(1)
        """
        self._posts.get_post(post_id)
        cleaned = content.strip()
        if not cleaned:
            raise ValidationError("Comment cannot be empty.")
        if len(cleaned) > self.MAX_COMMENT_LENGTH:
            raise ValidationError(
                f"Comment cannot exceed {self.MAX_COMMENT_LENGTH} characters."
            )

        parent_node: Comment | None = None
        if parent_comment_id is not None:
            parent_node = self._comments_by_id.get(parent_comment_id)
            if parent_node is None or parent_node.post_id != post_id:
                raise ResourceNotFoundError(
                    f"Parent comment '{parent_comment_id}' not found on post '{post_id}'."
                )

        cid = comment_id if comment_id is not None else f"cmt_{uuid.uuid4().hex[:10]}"
        comment = Comment(
            comment_id=cid,
            post_id=post_id,
            author=author,
            parent_comment_id=parent_comment_id,
            content=cleaned,
            created_at=created_at,
            seq_id=seq_id,
        )

        if parent_node is None:
            self._get_or_create_root_comments(post_id).append(comment)
        else:
            parent_node.replies.append(comment)

        self._comments_by_id.put(cid, comment)
        return comment

    def get_comment(self, comment_id: str) -> Comment:
        """Return a single Comment by ID or raise ResourceNotFoundError.

        Time: O(1) average
        Space: O(1)
        """
        comment: Comment | None = self._comments_by_id.get(comment_id)
        if comment is None:
            raise ResourceNotFoundError(f"Comment '{comment_id}' does not exist.")
        return comment

    def get_comments_preorder(self, post_id: str) -> list[tuple[Comment, int]]:
        """Traverse a post's comment tree using pre-order DFS and return `(comment, depth)`.

        Why pre-order DFS (Visit Node -> Visit Children left-to-right):
        - Every parent comment is displayed immediately before its nested replies,
          making threaded discussions natural to read.

        Time: O(C), where C is the total number of comments and replies on `post_id`
        Space: O(C) for the output list + O(H) recursion stack for tree height H
        """
        self._posts.get_post(post_id)
        roots: list[Comment] | None = self._root_comments_by_post.get(post_id)
        if roots is None:
            return []

        ordered: list[tuple[Comment, int]] = []

        def _preorder_dfs(node: Comment, depth: int) -> None:
            ordered.append((node, depth))
            for child in node.replies:
                _preorder_dfs(child, depth + 1)

        for root_comment in roots:
            _preorder_dfs(root_comment, 0)

        return ordered

    def comment_count(self, post_id: str) -> int:
        """Count total comments (including all nested replies) on `post_id`.

        Time: O(C), where C is total comments on `post_id`
        Space: O(H), where H is max reply nesting depth
        """
        roots: list[Comment] | None = self._root_comments_by_post.get(post_id)
        if roots is None:
            return 0

        def _count_subtree(node: Comment) -> int:
            total = 1
            for child in node.replies:
                total += _count_subtree(child)
            return total

        total_count = 0
        for root_comment in roots:
            total_count += _count_subtree(root_comment)
        return total_count

    def remove_post_engagement(self, post_id: str) -> None:
        """Remove all likes and comments associated with a deleted post.

        Time: O(C), where C is the number of comments on `post_id`
        Space: O(H)
        """
        if self._likes_by_post.contains(post_id):
            self._likes_by_post.remove(post_id)

        roots: list[Comment] | None = self._root_comments_by_post.get(post_id)
        if roots is not None:
            def _purge(node: Comment) -> None:
                if self._comments_by_id.contains(node.comment_id):
                    self._comments_by_id.remove(node.comment_id)
                for child in node.replies:
                    _purge(child)

            for root_comment in roots:
                _purge(root_comment)
            self._root_comments_by_post.remove(post_id)

    def get_trending_posts(
        self,
        username: str,
        now: float,
        k: int = 5,
        window_seconds: float = 7 * 86400.0,
    ) -> list[TrendingPost]:
        """Rank recent posts from `username`'s connections by `likes + 2 * comments` using MinHeap.

        Because each connection's post list is newest-first, traversal stops as soon as
        a post falls outside `[now - window_seconds, now]`.

        Time: O(R log R), where R is the number of recent posts across connections
        Space: O(R)
        """
        connections = self._graph.neighbors(username)
        if k <= 0 or not connections:
            return []

        cutoff = now - window_seconds
        ranked_heap = MinHeap(
            key=lambda item: (-item.score, -item.post.created_at, -item.post.seq_id)
        )

        for friend in connections:
            node = self._posts.get_user_post_head(friend)
            while node is not None:
                post = node.value
                # Early exit: remaining posts in this linked list are strictly older.
                if post.created_at < cutoff:
                    break
                likes = self.like_count(post.post_id)
                comments = self.comment_count(post.post_id)
                score = likes + 2 * comments
                ranked_heap.push(
                    TrendingPost(
                        post=post,
                        like_count=likes,
                        comment_count=comments,
                        score=score,
                    )
                )
                node = node.next

        trending: list[TrendingPost] = []
        while len(trending) < k and not ranked_heap.is_empty():
            trending.append(ranked_heap.pop())
        return trending
