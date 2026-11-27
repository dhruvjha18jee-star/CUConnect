# tests/test_communities.py
# Unit tests for core.communities.CommunityDetector (iterative DFS with Stack).

import unittest

from core.communities import CommunityDetector
from core.graph import SocialGraph


class TestCommunityDetector(unittest.TestCase):
    def test_connected_components_and_user_community(self) -> None:
        g = SocialGraph()
        for u in ["a", "b", "c", "d", "x", "y", "solo"]:
            g.add_user(u)
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        g.add_edge("c", "d")
        g.add_edge("x", "y")

        detector = CommunityDetector(g)
        communities = detector.find_all_communities()

        self.assertEqual(len(communities), 3)
        self.assertEqual(communities[0].members, ["a", "b", "c", "d"])
        self.assertEqual(communities[0].size, 4)
        self.assertEqual(communities[1].members, ["x", "y"])
        self.assertEqual(communities[1].size, 2)
        self.assertEqual(communities[2].members, ["solo"])
        self.assertEqual(communities[2].size, 1)

        user_comm = detector.get_user_community("y")
        self.assertEqual(user_comm.community_id, 2)
        self.assertEqual(user_comm.size, 2)
        self.assertEqual(user_comm.members, ["x", "y"])


if __name__ == "__main__":
    unittest.main()
