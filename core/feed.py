# core/feed.py
# Home feed built by k-way merging connections' newest-first post lists with MinHeap.
# Course mapping: Session 15: Heaps and Hash Tables & Session 4: Singly Linked Lists.

from core.ds.heap import MinHeap
from core.ds.linked_list import ListNode
from core.graph import SocialGraph
from core.models import Post
from core.posts import PostManager


class FeedEngine:
    """Produces a paginated, newest-first home feed from a user's connections.

    Why k-way merge with a MinHeap instead of collecting and sorting all posts:
    - Each connection's SinglyLinkedList is already sorted newest-first.
    - Putting only the current head pointer of each of the `k` connections into
      a max-heap (our MinHeap with negated timestamp & seq_id) keeps heap size
      bounded by `k`.
    - Extracting a page of `N` posts takes O((k + offset + N) log k) instead of
      collecting and sorting all P total posts in O(P log P).
    """

    def __init__(self, graph: SocialGraph, posts: PostManager) -> None:
        """Bind the feed engine to the social graph and post manager.

        Time: O(1)
        Space: O(1)
        """
        self._graph = graph
        self._posts = posts

    def get_home_feed(
        self,
        username: str,
        limit: int = 10,
        offset: int = 0,
        include_self: bool = False,
    ) -> tuple[list[Post], bool]:
        """Return `(posts_page, has_more)` for `username`'s home feed.

        Uses k-way merge over connections' SinglyLinkedList head pointers via MinHeap.
        Deterministic tie-breaking uses `(-post.created_at, -post.seq_id)`.

        Time: O((k + offset + limit) log k), where k is the number of connections
        Space: O(k + limit)
        """
        sources = self._graph.neighbors(username)
        if include_self:
            sources.append(username)

        if limit <= 0 or not sources:
            return [], False
        if offset < 0:
            offset = 0

        # Negate timestamp and seq_id so MinHeap pops the newest post first.
        heap = MinHeap(
            key=lambda node: (-node.value.created_at, -node.value.seq_id)
        )

        # Seed the heap with the newest post node from each connection who has posted.
        for author in sources:
            head_node: ListNode | None = self._posts.get_user_post_head(author)
            if head_node is not None:
                heap.push(head_node)

        page: list[Post] = []
        skipped = 0

        while not heap.is_empty() and len(page) < limit:
            top_node: ListNode = heap.pop()
            if top_node.next is not None:
                # Advance only the list whose post we just consumed.
                heap.push(top_node.next)

            if skipped < offset:
                skipped += 1
            else:
                page.append(top_node.value)

        has_more = not heap.is_empty()
        return page, has_more
