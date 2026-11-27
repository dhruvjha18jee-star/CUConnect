# core/search.py
# Prefix search index for users by username or any word of their full name using Trie.
# Course mapping: Session 8: Trees, Session 3: Arrays and Strings & Session 14: Merge Sort.

import re

from core.auth import AccountManager
from core.ds.algorithms import merge_sort
from core.ds.trie import Trie
from core.models import User

_TOKEN_SPLIT = re.compile(r"[^a-z0-9_]+")


def _extract_tokens(full_name: str) -> list[str]:
    """Split a full name into clean lowercase alphanumeric tokens for Trie indexing."""
    raw_parts = _TOKEN_SPLIT.split(full_name.lower())
    return [part for part in raw_parts if part]


class UserSearchIndex:
    """Indexes lowercase usernames and name words in a Trie for as-you-type search."""

    def __init__(self, accounts: AccountManager) -> None:
        """Create an empty Trie search index backed by `AccountManager`.

        Time: O(1)
        Space: O(1)
        """
        self._accounts = accounts
        self._trie = Trie()

    def index_user(self, user: User) -> None:
        """Insert a user's username and every word of their full name into the Trie.

        Time: O(L_total), where L_total is total characters across username + name words
        Space: O(L_total)
        """
        self._trie.insert(user.username, user.username)
        for token in _extract_tokens(user.full_name):
            self._trie.insert(token, user.username)

    def reindex_user(self, old_full_name: str, updated_user: User) -> None:
        """Update Trie tokens when a user edits their full name.

        Time: O(L_old + L_new)
        Space: O(L_new)
        """
        for old_token in _extract_tokens(old_full_name):
            self._trie.remove(old_token, updated_user.username)
        # Re-insert username as well in case an old name token equaled the username.
        self._trie.insert(updated_user.username, updated_user.username)
        for new_token in _extract_tokens(updated_user.full_name):
            self._trie.insert(new_token, updated_user.username)

    def search(self, prefix: str, limit: int = 10) -> list[User]:
        """Return up to `limit` Users matching `prefix` on username or name word.

        Results are sorted alphabetically by `(full_name.lower(), username)` via merge_sort.

        Time: O(L + M + U log U), where L = len(prefix), M = prefix subtree size,
              and U = number of matched users
        Space: O(M + U)
        """
        matched_usernames = self._trie.prefix_search(prefix)
        users = [self._accounts.get_user(uname) for uname in matched_usernames]
        ordered = merge_sort(users, key=lambda u: (u.full_name.lower(), u.username))
        if limit >= 0:
            return ordered[:limit]
        return ordered
