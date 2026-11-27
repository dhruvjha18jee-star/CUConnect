# tests/test_graph.py
# Unit tests for core.graph.SocialGraph (adjacency lists, mutuals, BFS degree & chain).

import unittest

from core.graph import SocialGraph
from core.models import ConnectionRuleError, UserNotFoundError, ValidationError


class TestSocialGraph(unittest.TestCase):
    def _build_chain_graph(self) -> SocialGraph:
        # Graph: a - b - c - d - e, plus a - f - c (diamond) and isolated z
        g = SocialGraph()
        for u in ["a", "b", "c", "d", "e", "f", "z"]:
            g.add_user(u)
        for u, v in [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"), ("a", "f"), ("f", "c")]:
            g.add_edge(u, v)
        return g

    def test_undirected_invariants_no_self_or_duplicate_edges(self) -> None:
        g = SocialGraph()
        g.add_user("a")
        g.add_user("b")
        with self.assertRaises(ValidationError):
            g.add_edge("a", "a")
        with self.assertRaises(UserNotFoundError):
            g.add_edge("a", "unknown")

        g.add_edge("a", "b")
        self.assertTrue(g.has_edge("a", "b"))
        self.assertTrue(g.has_edge("b", "a"))
        self.assertEqual(g.edge_count(), 1)

        with self.assertRaises(ConnectionRuleError):
            g.add_edge("b", "a")

        g.remove_edge("a", "b")
        self.assertFalse(g.has_edge("a", "b"))
        self.assertFalse(g.has_edge("b", "a"))
        self.assertEqual(g.edge_count(), 0)

        with self.assertRaises(ConnectionRuleError):
            g.remove_edge("a", "b")

    def test_mutual_connections(self) -> None:
        g = self._build_chain_graph()
        self.assertEqual(g.mutual_connections("a", "c"), ["b", "f"])
        self.assertEqual(g.mutual_connections("a", "e"), [])

    def test_bfs_degrees_labels_and_shortest_path(self) -> None:
        g = self._build_chain_graph()

        r0 = g.degree_and_shortest_path("a", "a")
        self.assertEqual((r0.distance, r0.label, r0.path), (0, "Self", ["a"]))

        r1 = g.degree_and_shortest_path("a", "b")
        self.assertEqual((r1.distance, r1.label, r1.path), (1, "1st", ["a", "b"]))

        r2 = g.degree_and_shortest_path("a", "c")
        self.assertEqual((r2.distance, r2.label, r2.path), (2, "2nd", ["a", "b", "c"]))

        r3 = g.degree_and_shortest_path("a", "d")
        self.assertEqual((r3.distance, r3.label, r3.path), (3, "3rd", ["a", "b", "c", "d"]))

        r4 = g.degree_and_shortest_path("a", "e")
        self.assertEqual((r4.distance, r4.label, r4.path), (4, "3+", ["a", "b", "c", "d", "e"]))

        rz = g.degree_and_shortest_path("a", "z")
        self.assertEqual((rz.distance, rz.label, rz.path), (None, "Not connected", []))


if __name__ == "__main__":
    unittest.main()
