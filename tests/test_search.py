# tests/test_search.py
# Unit tests for core.search.UserSearchIndex (Trie indexing username + name words).

import unittest

from core.auth import AccountManager
from core.search import UserSearchIndex


class TestUserSearchIndex(unittest.TestCase):
    def test_search_by_username_and_name_words_and_reindex(self) -> None:
        am = AccountManager()
        idx = UserSearchIndex(am)

        u1 = am.register_user("aarav_s", "pass1234", "Aarav Sharma", "CSAI", 2)
        u2 = am.register_user("diya_n", "pass1234", "Diya Nair", "EVE", 2)
        u3 = am.register_user("sharma_k", "pass1234", "Kabir Verma", "EECS", 3)

        for u in [u1, u2, u3]:
            idx.index_user(u)

        # Prefix matches both Aarav Sharma (last name) and sharma_k (username).
        res = idx.search("sha")
        self.assertEqual([u.username for u in res], ["aarav_s", "sharma_k"])

        # Prefix matches Diya by last name token 'nair'.
        self.assertEqual([u.username for u in idx.search("nai")], ["diya_n"])

        # Reindex after name edit removes old name token and indexes new one.
        old_name = u2.full_name
        am.update_profile("diya_n", full_name="Diya Menon")
        idx.reindex_user(old_name, u2)
        self.assertEqual(idx.search("nai"), [])
        self.assertEqual([u.username for u in idx.search("men")], ["diya_n"])


if __name__ == "__main__":
    unittest.main()
