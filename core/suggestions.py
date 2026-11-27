# core/suggestions.py
# "People You May Know" via Depth-2 BFS, Jaccard Coefficient, and MinHeap top-k ranking.
# Course mapping: Session 11: Graphs (BFS) & Session 15: Heaps and Hash Tables (MinHeap).

from core.auth import AccountManager
from core.connections import ConnectionManager
from core.ds.heap import MinHeap
from core.ds.queue_ds import Queue
from core.graph import SocialGraph
from core.models import Suggestion


class SuggestionEngine:
    """Recommends 2nd-degree connections ranked by Jaccard neighbourhood overlap.

    Algorithm:
    1. Run BFS to depth 2 from `username` using our hand-written Queue.
       Every node at exact distance 2 is a friend-of-a-friend not yet connected
       to `username`.
    2. For each candidate `v`, compute the Jaccard coefficient:
           J(u, v) = |N(u) ∩ N(v)| / |N(u) ∪ N(v)|
       where |N(u) ∪ N(v)| = deg(u) + deg(v) - |N(u) ∩ N(v)|.
    3. Rank candidates using our MinHeap configured as a max-heap on
       `(-jaccard_score, -mutual_count, username)` and pop the top `k`.
    """

    def __init__(
        self,
        graph: SocialGraph,
        accounts: AccountManager,
        connections: ConnectionManager,
    ) -> None:
        """Initialize the suggestion engine with graph, account, and request managers.

        Time: O(1)
        Space: O(1)
        """
        self._graph = graph
        self._accounts = accounts
        self._connections = connections

    def recommend(
        self,
        username: str,
        k: int = 5,
        exclude_pending: bool = True,
    ) -> list[Suggestion]:
        """Return up to `k` 'People You May Know' suggestions for `username`.

        Time: O(sum_{w in N(u)} deg(w) + C * (deg(u) + deg(c)) + C log C)
              where C is the number of unique depth-2 candidates.
        Space: O(deg(u) + C)
        """
        # Verify user exists before starting BFS.
        self._accounts.get_user(username)
        if k <= 0:
            return []

        user_deg = self._graph.degree(username)
        if user_deg == 0:
            return []

        # Depth-limited BFS (depth 0 -> 1 -> 2) using our hand-written Queue.
        visited: set[str] = {username}
        depth_two_candidates: list[str] = []
        queue: Queue = Queue()
        queue.enqueue((username, 0))

        while not queue.is_empty():
            current, depth = queue.dequeue()
            if depth >= 2:
                continue

            for neighbor in self._graph.neighbors(current):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                next_depth = depth + 1
                if next_depth == 2:
                    depth_two_candidates.append(neighbor)
                else:
                    queue.enqueue((neighbor, next_depth))

        # Score each depth-2 candidate with Jaccard similarity and push into our MinHeap.
        # Negating jaccard_score and mutual_count turns MinHeap into a max-heap;
        # `username` breaks exact ties alphabetically for 100% deterministic output.
        ranked_heap = MinHeap(
            key=lambda s: (-s.jaccard_score, -s.mutual_count, s.username)
        )

        for candidate in depth_two_candidates:
            if exclude_pending and self._connections.has_any_pending_between(username, candidate):
                continue

            mutuals = self._graph.mutual_connections(username, candidate)
            mutual_count = len(mutuals)
            if mutual_count == 0:
                continue

            candidate_deg = self._graph.degree(candidate)
            union_size = user_deg + candidate_deg - mutual_count
            jaccard = mutual_count / union_size if union_size > 0 else 0.0

            profile = self._accounts.get_user(candidate)
            ranked_heap.push(
                Suggestion(
                    username=candidate,
                    full_name=profile.full_name,
                    programme=profile.programme,
                    year=profile.year,
                    jaccard_score=round(jaccard, 4),
                    mutual_count=mutual_count,
                    mutual_usernames=mutuals,
                )
            )

        results: list[Suggestion] = []
        while len(results) < k and not ranked_heap.is_empty():
            results.append(ranked_heap.pop())
        return results
