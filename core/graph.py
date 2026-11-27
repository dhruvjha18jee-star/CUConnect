# core/graph.py
# Undirected social network graph G(V, E) stored as adjacency lists in a HashTable.
# Course mapping: Session 11: Graphs (Adjacency Lists, BFS) & Session 12: Binary Search.

from core.ds.algorithms import binary_search, merge_sort
from core.ds.hash_table import HashTable
from core.ds.queue_ds import Queue
from core.models import ConnectionRuleError, DegreeResult, UserNotFoundError, ValidationError


class SocialGraph:
    """Undirected simple graph G(V, E) modelling accepted student connections.

    Invariants enforced by every mutator:
    - No self-loops: (u, u) is rejected.
    - No parallel/duplicate edges: each unordered pair {u, v} appears at most once.
    - Symmetry: v is in adj[u] if and only if u is in adj[v].

    Why adjacency lists instead of an adjacency matrix:
    - Social graphs are sparse (each student connects to ~10-50 peers, not all V
      students). Adjacency lists use O(V + E) space instead of O(V^2), and
      iterating over a user's connections takes O(deg(u)) instead of O(V).
    - Keeping each neighbour list sorted enables O(log deg(u)) edge checks via
      binary_search and O(deg(u) + deg(v)) mutual-connection intersection.
    """

    def __init__(self) -> None:
        """Create an empty social graph.

        Time: O(1)
        Space: O(1)
        """
        self._adj: HashTable = HashTable(initial_capacity=32)
        self._edge_count: int = 0

    def _require_user(self, username: str) -> list[str]:
        """Return the adjacency list for `username` or raise UserNotFoundError."""
        neighbors: list[str] | None = self._adj.get(username)
        if neighbors is None:
            raise UserNotFoundError(f"User '{username}' does not exist in the graph.")
        return neighbors

    def _insert_sorted(self, neighbors: list[str], target: str) -> None:
        """Insert `target` into a sorted adjacency list while maintaining sorted order."""
        pos = len(neighbors)
        for i in range(len(neighbors)):
            if target < neighbors[i]:
                pos = i
                break
        neighbors.insert(pos, target)

    def add_user(self, username: str) -> None:
        """Add a vertex `username` with an empty adjacency list (idempotent).

        Time: O(1) average
        Space: O(1)
        """
        if not self._adj.contains(username):
            self._adj.put(username, [])

    def has_user(self, username: str) -> bool:
        """Return True if vertex `username` exists in the graph.

        Time: O(1) average
        Space: O(1)
        """
        return self._adj.contains(username)

    def has_edge(self, user_a: str, user_b: str) -> bool:
        """Return True if an undirected connection exists between `user_a` and `user_b`.

        Uses our hand-written binary_search on `user_a`'s sorted adjacency list.

        Time: O(log deg(user_a))
        Space: O(1)
        """
        neighbors_a = self._require_user(user_a)
        self._require_user(user_b)
        return binary_search(neighbors_a, user_b) != -1

    def add_edge(self, user_a: str, user_b: str) -> None:
        """Add an undirected edge between `user_a` and `user_b`.

        Rejects self-edges and duplicate edges.

        Time: O(deg(user_a) + deg(user_b))
        Space: O(1)
        """
        if user_a == user_b:
            raise ValidationError("A user cannot connect with themselves.")
        neighbors_a = self._require_user(user_a)
        neighbors_b = self._require_user(user_b)

        if binary_search(neighbors_a, user_b) != -1:
            raise ConnectionRuleError(f"'{user_a}' and '{user_b}' are already connected.")

        self._insert_sorted(neighbors_a, user_b)
        self._insert_sorted(neighbors_b, user_a)
        self._edge_count += 1

    def remove_edge(self, user_a: str, user_b: str) -> None:
        """Remove both directions of the undirected edge between `user_a` and `user_b`.

        Time: O(deg(user_a) + deg(user_b))
        Space: O(1)
        """
        neighbors_a = self._require_user(user_a)
        neighbors_b = self._require_user(user_b)

        idx_b = binary_search(neighbors_a, user_b)
        if idx_b == -1:
            raise ConnectionRuleError(f"'{user_a}' and '{user_b}' are not connected.")

        idx_a = binary_search(neighbors_b, user_a)
        neighbors_a.pop(idx_b)
        if idx_a != -1:
            neighbors_b.pop(idx_a)
        self._edge_count -= 1

    def neighbors(self, username: str) -> list[str]:
        """Return an alphabetically sorted copy of `username`'s direct connections.

        Time: O(deg(username))
        Space: O(deg(username))
        """
        return list(self._require_user(username))

    def degree(self, username: str) -> int:
        """Return the number of direct connections (degree) of `username`.

        Time: O(1) average
        Space: O(1)
        """
        return len(self._require_user(username))

    def users(self) -> list[str]:
        """Return all usernames in the graph sorted alphabetically via merge_sort.

        Time: O(V log V)
        Space: O(V)
        """
        return merge_sort(self._adj.keys())

    def user_count(self) -> int:
        """Return |V|, the number of users in the graph.

        Time: O(1)
        Space: O(1)
        """
        return len(self._adj)

    def edge_count(self) -> int:
        """Return |E|, the number of undirected connections in the graph.

        Time: O(1)
        Space: O(1)
        """
        return self._edge_count

    def mutual_connections(self, user_a: str, user_b: str) -> list[str]:
        """Return the sorted list of mutual connections shared by `user_a` and `user_b`.

        Because both adjacency lists are maintained in alphabetical order, we use a
        classic two-pointer sorted-list intersection in linear time without extra hashing.

        Time: O(deg(user_a) + deg(user_b))
        Space: O(min(deg(user_a), deg(user_b)))
        """
        neighbors_a = self._require_user(user_a)
        neighbors_b = self._require_user(user_b)

        mutuals: list[str] = []
        i = 0
        j = 0
        len_a = len(neighbors_a)
        len_b = len(neighbors_b)

        while i < len_a and j < len_b:
            if neighbors_a[i] == neighbors_b[j]:
                mutuals.append(neighbors_a[i])
                i += 1
                j += 1
            elif neighbors_a[i] < neighbors_b[j]:
                i += 1
            else:
                j += 1

        return mutuals

    def _format_degree_label(self, distance: int | None) -> str:
        """Convert hop distance to the required display label (1st, 2nd, 3rd, 3+)."""
        if distance is None:
            return "Not connected"
        if distance == 0:
            return "Self"
        if distance == 1:
            return "1st"
        if distance == 2:
            return "2nd"
        if distance == 3:
            return "3rd"
        return "3+"

    def degree_and_shortest_path(self, source: str, target: str) -> DegreeResult:
        """Find degree of connection and one shortest path from `source` to `target` using BFS.

        Why BFS instead of DFS:
        - In an unweighted graph, BFS explores vertices layer by layer (distance 0, 1, 2, ...),
          so the very first time we reach `target` is guaranteed to be a shortest path.
        - Because adjacency lists are sorted alphabetically, BFS visits neighbours in a
          deterministic order and always returns the lexicographically earliest shortest chain.

        Time: O(V + E)
        Space: O(V)
        """
        self._require_user(source)
        self._require_user(target)

        if source == target:
            return DegreeResult(
                source=source,
                target=target,
                distance=0,
                label="Self",
                path=[source],
            )

        visited: set[str] = {source}
        parent: dict[str, str | None] = {source: None}
        frontier: Queue = Queue()
        frontier.enqueue(source)

        found = False
        while not frontier.is_empty():
            current: str = frontier.dequeue()
            for neighbor in self._require_user(current):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                parent[neighbor] = current
                if neighbor == target:
                    found = True
                    break
                frontier.enqueue(neighbor)
            if found:
                break

        if not found:
            return DegreeResult(
                source=source,
                target=target,
                distance=None,
                label="Not connected",
                path=[],
            )

        # Reconstruct the shortest path from target back to source via the parent map.
        reversed_path: list[str] = []
        node: str | None = target
        while node is not None:
            reversed_path.append(node)
            node = parent[node]
        reversed_path.reverse()

        distance = len(reversed_path) - 1
        return DegreeResult(
            source=source,
            target=target,
            distance=distance,
            label=self._format_degree_label(distance),
            path=reversed_path,
        )
