# tests/test_feed.py
# Unit tests for core.feed.FeedEngine (k-way merge with MinHeap and paging).

import unittest

from core.feed import FeedEngine
from core.graph import SocialGraph
from core.posts import PostManager


class TestFeedEngine(unittest.TestCase):
    def test_k_way_merge_newest_first_and_paging(self) -> None:
        graph = SocialGraph()
        pm = PostManager()
        for u in ["aarav", "diya", "rohan", "stranger"]:
            graph.add_user(u)
            pm.register_user(u)

        graph.add_edge("aarav", "diya")
        graph.add_edge("aarav", "rohan")

        # Posts created in chronological order across connections + stranger + self.
        p1 = pm.create_post("diya", "Diya 1", 100.0, 1)
        p2 = pm.create_post("rohan", "Rohan 1", 200.0, 2)
        pm.create_post("stranger", "Stranger post (should not show)", 250.0, 3)
        p3 = pm.create_post("diya", "Diya 2", 300.0, 4)
        # Same timestamp tie-break via seq_id!
        p4 = pm.create_post("rohan", "Rohan 2", 300.0, 5)
        pm.create_post("aarav", "Own post (excluded by default)", 400.0, 6)

        feed = FeedEngine(graph, pm)
        page1, more1 = feed.get_home_feed("aarav", limit=2, offset=0)
        self.assertTrue(more1)
        self.assertEqual([p.post_id for p in page1], [p4.post_id, p3.post_id])

        page2, more2 = feed.get_home_feed("aarav", limit=2, offset=2)
        self.assertFalse(more2)
        self.assertEqual([p.post_id for p in page2], [p2.post_id, p1.post_id])

        # Verify own post appears only if include_self=True.
        with_self, _ = feed.get_home_feed("aarav", limit=10, offset=0, include_self=True)
        self.assertEqual(len(with_self), 5)
        self.assertEqual(with_self[0].author, "aarav")


if __name__ == "__main__":
    unittest.main()
