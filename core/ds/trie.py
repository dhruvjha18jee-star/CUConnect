# core/ds/trie.py
# Hand-written Prefix Tree (Trie) for fast as-you-type user search suggestions.
# Course mapping: Session 8: Trees & Session 3: Arrays and Strings (Prefix Search).

from core.ds.algorithms import merge_sort
from core.ds.hash_table import HashTable
from core.ds.stack import Stack


class TrieNode:
    """Single character node inside the Trie.

    Each node uses our hand-written HashTable to map next characters to child
    TrieNodes, and stores the set of user IDs whose indexed token ends here.
    """

    def __init__(self) -> None:
        """Create an empty TrieNode with a compact HashTable of child links.

        Time: O(1)
        Space: O(1)
        """
        # Small initial capacity keeps memory compact because most nodes have few children.
        self.children: HashTable = HashTable(initial_capacity=4)
        self.user_ids: set[str] = set()


class Trie:
    """Prefix Tree mapping lowercase words (usernames and name tokens) to user IDs.

    Why a Trie instead of scanning every user with `startswith`:
    - Walking the prefix takes O(L) time where L is the prefix length, completely
      independent of how many total users exist in the platform.
    - All matching completions live in the subtree rooted at the prefix node.
    """

    def __init__(self) -> None:
        """Create an empty Trie with a root node.

        Time: O(1)
        Space: O(1)
        """
        self._root: TrieNode = TrieNode()

    def insert(self, word: str, user_id: str) -> None:
        """Index `word` (case-insensitive) so prefix searches can find `user_id`.

        Time: O(L), where L = len(word)
        Space: O(L) for newly created nodes
        """
        cleaned = word.strip().lower()
        if not cleaned:
            return

        current = self._root
        for ch in cleaned:
            child = current.children.get(ch)
            if child is None:
                child = TrieNode()
                current.children.put(ch, child)
            current = child

        current.user_ids.add(user_id)

    def remove(self, word: str, user_id: str) -> bool:
        """Remove the association between `word` and `user_id`, pruning empty nodes.

        Returns True if `user_id` was present under `word`, False otherwise.

        Time: O(L), where L = len(word)
        Space: O(L) for the path stack used to prune empty nodes
        """
        cleaned = word.strip().lower()
        if not cleaned:
            return False

        # Track the traversed path on our Stack so we can prune dead branches bottom-up.
        path: Stack = Stack()
        current = self._root
        for ch in cleaned:
            child = current.children.get(ch)
            if child is None:
                return False
            path.push((current, ch, child))
            current = child

        if user_id not in current.user_ids:
            return False

        current.user_ids.remove(user_id)

        # Prune any node that now holds no user IDs and has no remaining children.
        while not path.is_empty():
            parent, ch, child = path.pop()
            if not child.user_ids and len(child.children) == 0:
                parent.children.remove(ch)
            else:
                break

        return True

    def prefix_search(self, prefix: str, limit: int | None = None) -> list[str]:
        """Return sorted unique user IDs matching any indexed word starting with `prefix`.

        An empty prefix returns an empty list so callers do not accidentally dump
        the entire directory on a blank search box.

        Time: O(L + M + U log U), where L = len(prefix), M = nodes in prefix subtree,
              and U = number of matched unique user IDs
        Space: O(M + U)
        """
        cleaned = prefix.strip().lower()
        if not cleaned:
            return []

        current = self._root
        for ch in cleaned:
            child = current.children.get(ch)
            if child is None:
                return []
            current = child

        # Collect all user IDs in this subtree using iterative DFS with our Stack.
        matched: set[str] = set()
        dfs_stack: Stack = Stack()
        dfs_stack.push(current)

        while not dfs_stack.is_empty():
            node: TrieNode = dfs_stack.pop()
            for uid in node.user_ids:
                matched.add(uid)
            for child_node in node.children.values():
                dfs_stack.push(child_node)

        ordered = merge_sort(list(matched))
        if limit is not None and limit >= 0:
            return ordered[:limit]
        return ordered
