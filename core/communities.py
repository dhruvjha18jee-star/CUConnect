# core/communities.py
# Connected-components community detection via iterative DFS using our hand-written Stack.
# Course mapping: Session 11: Graphs (DFS) & Session 6: Stacks.

from core.ds.algorithms import merge_sort
from core.ds.stack import Stack
from core.graph import SocialGraph
from core.models import CommunityInfo, UserNotFoundError


class CommunityDetector:
    """Identifies student communities as connected components of the social graph.

    Why iterative DFS with our own Stack instead of recursion:
    - Avoids Python's recursion depth limit on large networks (e.g. 5,000+ users).
    - Explicitly demonstrates how DFS uses a LIFO Stack, contrasting directly
      with BFS's FIFO Queue in `core/graph.py`.
    """

    def __init__(self, graph: SocialGraph) -> None:
        """Bind community detection to a SocialGraph.

        Time: O(1)
        Space: O(1)
        """
        self._graph = graph

    def _dfs_component(self, start_user: str, visited: set[str]) -> list[str]:
        """Collect all vertices reachable from `start_user` using iterative DFS + Stack."""
        component: list[str] = []
        stack: Stack = Stack()
        visited.add(start_user)
        stack.push(start_user)

        while not stack.is_empty():
            current: str = stack.pop()
            component.append(current)
            for neighbor in self._graph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.push(neighbor)

        return merge_sort(component)

    def find_all_communities(self) -> list[CommunityInfo]:
        """Return all connected components sorted by descending size (ties alphabetically).

        Time: O(V log V + E)
        Space: O(V)
        """
        visited: set[str] = set()
        raw_components: list[list[str]] = []

        for username in self._graph.users():
            if username not in visited:
                members = self._dfs_component(username, visited)
                raw_components.append(members)

        ordered = merge_sort(raw_components, key=lambda m: (-len(m), m[0]))
        communities: list[CommunityInfo] = []
        for idx, members in enumerate(ordered, start=1):
            communities.append(
                CommunityInfo(
                    community_id=idx,
                    members=members,
                    size=len(members),
                )
            )
        return communities

    def get_user_community(self, username: str) -> CommunityInfo:
        """Return the CommunityInfo containing `username` (with its community ID and size).

        Time: O(V log V + E)
        Space: O(V)
        """
        if not self._graph.has_user(username):
            raise UserNotFoundError(f"User '{username}' does not exist.")

        for community in self.find_all_communities():
            if username in community.members:
                return community

        # Unreachable because every registered user is in at least a size-1 component.
        return CommunityInfo(community_id=1, members=[username], size=1)
