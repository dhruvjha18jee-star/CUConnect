# tests/test_engagement.py
# Unit tests for core.engagement.EngagementManager (likes, comment tree DFS, trending).

import unittest

from core.engagement import EngagementManager
from core.graph import SocialGraph
from core.posts import PostManager


class TestEngagementManager(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = SocialGraph()
        self.posts = PostManager()
        for u in ["aarav", "diya", "rohan"]:
            self.graph.add_user(u)
            self.posts.register_user(u)
        self.graph.add_edge("aarav", "diya")
        self.graph.add_edge("aarav", "rohan")
        self.eng = EngagementManager(self.graph, self.posts)

    def test_likes_and_nested_comment_preorder_dfs(self) -> None:
        p = self.posts.create_post("diya", "Built an FPGA UART core!", 100.0, 1)

        self.assertTrue(self.eng.like_post(p.post_id, "aarav", 101.0))
        self.assertFalse(self.eng.like_post(p.post_id, "aarav", 102.0))  # idempotent
        self.assertTrue(self.eng.like_post(p.post_id, "rohan", 103.0))
        self.assertEqual(self.eng.like_count(p.post_id), 2)
        self.assertEqual(self.eng.get_likers(p.post_id), ["aarav", "rohan"])

        self.assertTrue(self.eng.unlike_post(p.post_id, "rohan"))
        self.assertEqual(self.eng.like_count(p.post_id), 1)

        # Build nested comment tree:
        # c1 (depth 0)
        #   r1 (depth 1)
        #     r1_1 (depth 2)
        #   r2 (depth 1)
        # c2 (depth 0)
        c1 = self.eng.add_comment(p.post_id, "aarav", "Awesome!", 110.0, 2)
        c2 = self.eng.add_comment(p.post_id, "rohan", "Share the repo!", 111.0, 3)
        r1 = self.eng.add_comment(p.post_id, "diya", "Thanks Aarav!", 112.0, 4, parent_comment_id=c1.comment_id)
        r1_1 = self.eng.add_comment(p.post_id, "aarav", "Will test on board", 113.0, 5, parent_comment_id=r1.comment_id)
        r2 = self.eng.add_comment(p.post_id, "rohan", "Nice baud rate", 114.0, 6, parent_comment_id=c1.comment_id)

        dfs_list = self.eng.get_comments_preorder(p.post_id)
        self.assertEqual(
            [(c.comment_id, depth) for c, depth in dfs_list],
            [
                (c1.comment_id, 0),
                (r1.comment_id, 1),
                (r1_1.comment_id, 2),
                (r2.comment_id, 1),
                (c2.comment_id, 0),
            ],
        )
        self.assertEqual(self.eng.comment_count(p.post_id), 5)

    def test_trending_posts_formula_and_recency_window(self) -> None:
        now = 1_000_000.0
        old_post = self.posts.create_post("diya", "Very old post", now - 20 * 86400, 1)
        p_mid = self.posts.create_post("diya", "Recent post A", now - 3600, 2)
        p_hot = self.posts.create_post("rohan", "Recent post B", now - 1800, 3)

        # Even if old_post has huge engagement, it falls outside the 7-day window.
        self.eng.like_post(old_post.post_id, "aarav", now - 19 * 86400)
        self.eng.add_comment(old_post.post_id, "aarav", "Old comment", now - 19 * 86400, 4)

        # p_mid: 2 likes + 2*0 comments = score 2
        self.eng.like_post(p_mid.post_id, "aarav", now - 1000)
        self.eng.like_post(p_mid.post_id, "rohan", now - 900)

        # p_hot: 1 like + 2*2 comments = score 5
        self.eng.like_post(p_hot.post_id, "aarav", now - 800)
        self.eng.add_comment(p_hot.post_id, "aarav", "Great!", now - 700, 5)
        self.eng.add_comment(p_hot.post_id, "diya", "Agreed!", now - 600, 6)

        trending = self.eng.get_trending_posts("aarav", now=now, k=5)
        self.assertEqual([t.post.post_id for t in trending], [p_hot.post_id, p_mid.post_id])
        self.assertEqual(trending[0].score, 5)
        self.assertEqual(trending[1].score, 2)


if __name__ == "__main__":
    unittest.main()
