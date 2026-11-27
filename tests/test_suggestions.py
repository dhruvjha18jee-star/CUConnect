# tests/test_suggestions.py
# Unit tests for core.suggestions.SuggestionEngine (Depth-2 BFS + Jaccard + MinHeap).

import unittest

from core.auth import AccountManager
from core.connections import ConnectionManager
from core.graph import SocialGraph
from core.suggestions import SuggestionEngine


class TestSuggestionEngine(unittest.TestCase):
    def test_jaccard_ranking_and_mutual_counts(self) -> None:
        accounts = AccountManager()
        graph = SocialGraph()
        cm = ConnectionManager(graph)

        for uname, name in [
            ("aarav", "Aarav"),
            ("diya", "Diya"),
            ("rohan", "Rohan"),
            ("meera", "Meera"),
            ("kabir", "Kabir"),
            ("vikram", "Vikram"),
        ]:
            accounts.register_user(uname, "pass1234", name, "CSAI", 2)
            graph.add_user(uname)
            cm.register_user(uname)

        # aarav connects to diya, rohan
        # meera connects to diya, rohan -> mutuals={diya, rohan}=2, union=2 -> J=1.0
        # kabir connects to diya, vikram -> mutuals={diya}=1, union={diya, rohan, vikram}=3 -> J=1/3=0.3333
        # vikram is at depth 3 from aarav -> must NOT appear in depth-2 suggestions!
        for u, v in [
            ("aarav", "diya"),
            ("aarav", "rohan"),
            ("meera", "diya"),
            ("meera", "rohan"),
            ("kabir", "diya"),
            ("kabir", "vikram"),
        ]:
            graph.add_edge(u, v)

        engine = SuggestionEngine(graph, accounts, cm)
        recs = engine.recommend("aarav", k=5)

        self.assertEqual([r.username for r in recs], ["meera", "kabir"])
        self.assertAlmostEqual(recs[0].jaccard_score, 1.0, places=4)
        self.assertEqual(recs[0].mutual_count, 2)
        self.assertEqual(recs[0].mutual_usernames, ["diya", "rohan"])

        self.assertAlmostEqual(recs[1].jaccard_score, 1 / 3, places=4)
        self.assertEqual(recs[1].mutual_count, 1)
        self.assertEqual(recs[1].mutual_usernames, ["diya"])

        # Top-1 returns only meera
        top1 = engine.recommend("aarav", k=1)
        self.assertEqual([r.username for r in top1], ["meera"])

        # Pending request excludes candidate by default
        cm.send_request("aarav", "meera", 10.0, 1)
        recs_after_req = engine.recommend("aarav", k=5)
        self.assertEqual([r.username for r in recs_after_req], ["kabir"])


if __name__ == "__main__":
    unittest.main()
