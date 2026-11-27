# core/posts.py
# Per-user text posts stored in SinglyLinkedLists (newest at head) inside a HashTable.
# Course mapping: Session 4: Singly Linked Lists & Session 15: Heaps and Hash Tables.

import uuid

from core.ds.hash_table import HashTable
from core.ds.linked_list import ListNode, SinglyLinkedList
from core.models import (
    AuthorizationError,
    Post,
    ResourceNotFoundError,
    UserNotFoundError,
    ValidationError,
)


class PostManager:
    """Stores each student's text posts in a newest-first SinglyLinkedList.

    Why a SinglyLinkedList per user:
    - Creating a new post prepends at the head in O(1) time.
    - Because every user's list stays naturally ordered newest-first, FeedEngine
      can run a k-way merge directly from each connection's `head` pointer
      without ever sorting all posts in the database.
    """

    MAX_CONTENT_LENGTH = 2000

    def __init__(self) -> None:
        """Create empty per-user post lists and a post-ID index.

        Time: O(1)
        Space: O(1)
        """
        self._user_posts: HashTable = HashTable(initial_capacity=32)
        self._posts_by_id: HashTable = HashTable(initial_capacity=64)

    def register_user(self, username: str) -> None:
        """Initialize an empty SinglyLinkedList of posts for a new user.

        Time: O(1) average
        Space: O(1)
        """
        if not self._user_posts.contains(username):
            self._user_posts.put(username, SinglyLinkedList())

    def _require_list(self, username: str) -> SinglyLinkedList:
        """Return the user's post linked list or raise UserNotFoundError."""
        post_list: SinglyLinkedList | None = self._user_posts.get(username)
        if post_list is None:
            raise UserNotFoundError(f"User '{username}' does not exist.")
        return post_list

    def create_post(
        self,
        author: str,
        content: str,
        created_at: float,
        seq_id: int,
        post_id: str | None = None,
        image_path: str | None = None,
    ) -> Post:
        """Validate and prepend a new post (with optional image) to `author`'s SinglyLinkedList.

        Time: O(1) average
        Space: O(1)
        """
        post_list = self._require_list(author)
        cleaned = content.strip()
        if not cleaned:
            raise ValidationError("Post content cannot be empty.")
        if len(cleaned) > self.MAX_CONTENT_LENGTH:
            raise ValidationError(
                f"Post content cannot exceed {self.MAX_CONTENT_LENGTH} characters."
            )

        clean_img = image_path.strip() if image_path and image_path.strip() else None
        pid = post_id if post_id is not None else f"post_{uuid.uuid4().hex[:10]}"
        post = Post(
            post_id=pid,
            author=author,
            content=cleaned,
            created_at=created_at,
            seq_id=seq_id,
            image_path=clean_img,
        )
        post_list.insert_head(post)
        self._posts_by_id.put(pid, post)
        return post

    def load_post(self, post: Post) -> None:
        """Insert a persisted Post at the head of its author's list during startup hydration.

        Callers must pass posts sorted oldest-to-newest so newest ends up at head.

        Time: O(1) average
        Space: O(1)
        """
        post_list = self._require_list(post.author)
        post_list.insert_head(post)
        self._posts_by_id.put(post.post_id, post)

    def get_post(self, post_id: str) -> Post:
        """Look up a single post by ID in O(1) average time.

        Time: O(1) average
        Space: O(1)
        """
        post: Post | None = self._posts_by_id.get(post_id)
        if post is None:
            raise ResourceNotFoundError(f"Post '{post_id}' does not exist.")
        return post

    def get_user_posts(self, username: str) -> list[Post]:
        """Return all posts authored by `username` in newest-first order.

        Time: O(P_u), where P_u is the number of posts by `username`
        Space: O(P_u)
        """
        return self._require_list(username).traverse()

    def get_user_post_head(self, username: str) -> ListNode | None:
        """Return the head ListNode of `username`'s post list for k-way merging.

        Time: O(1) average
        Space: O(1)
        """
        return self._require_list(username).head

    def delete_post(self, actor: str, post_id: str) -> Post:
        """Delete a post if and only if `actor` is its author.

        Time: O(P_author) to unlink from the author's SinglyLinkedList
        Space: O(1)
        """
        post = self.get_post(post_id)
        if post.author != actor:
            raise AuthorizationError("You can only delete your own posts.")

        post_list = self._require_list(actor)
        post_list.delete_by_id(post_id, lambda item: item.post_id)
        self._posts_by_id.remove(post_id)
        return post

    def total_posts(self) -> int:
        """Return the total number of posts across all users.

        Time: O(1)
        Space: O(1)
        """
        return len(self._posts_by_id)
