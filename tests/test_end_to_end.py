# tests/test_end_to_end.py
# Full end-to-end journey test verifying every CUConnect core requirement and enhancement.

import os
import tempfile
import unittest

from core.models import AuthorizationError, ConnectionRuleError, UserNotFoundError, ValidationError
from core.service import CUConnectService


class StepClock:
    def __init__(self, start: float = 1_760_000_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        self.now += 60.0
        return self.now


class TestEndToEnd(unittest.TestCase):
    def test_complete_cuconnect_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "e2e.db")
            clock = StepClock()
            svc = CUConnectService(db_path, clock=clock)

            # 1. Sign up 8 students (6 in main network across 4 hops, 2 in separate community)
            students = [
                ("aarav", "Aarav Sharma", "B.Tech CSAI", 2, ["Python", "ML"]),
                ("diya", "Diya Nair", "B.Tech CSAI", 2, ["DSA", "PyTorch"]),
                ("rohan", "Rohan Verma", "B.Tech EECS", 3, ["C++", "ROS"]),
                ("meera", "Meera Iyer", "B.Tech CSAI", 3, ["Python", "NLP"]),
                ("kabir", "Kabir Menon", "B.Tech EVE", 3, ["Verilog", "FPGA"]),
                ("vikram", "Vikram Rao", "B.Tech EECS", 4, ["Embedded", "RTOS"]),
                ("ananya", "Ananya Das", "B.Tech EVE", 1, ["Arduino", "PCB"]),
                ("sneha", "Sneha Joshi", "B.Tech EVE", 1, ["Sensors", "C"]),
            ]
            for uname, name, prog, yr, skills in students:
                svc.sign_up(uname, "chanakya2026", name, prog, yr, bio=f"{prog} student", skills=skills)

            # 2. Login, edit profile, logout
            svc.login("aarav", "chanakya2026")
            self.assertTrue(svc.is_logged_in("aarav"))
            svc.update_profile("aarav", bio="Building CUConnect in pure Python DSA!")
            self.assertEqual(svc.get_profile("aarav").bio, "Building CUConnect in pure Python DSA!")

            # 3. Connection workflow + edge cases
            with self.assertRaises(ValidationError):
                svc.send_connection_request("aarav", "aarav")
            with self.assertRaises(UserNotFoundError):
                svc.send_connection_request("aarav", "nonexistent")

            # Reverse request auto-accept: diya -> aarav, then aarav -> diya
            self.assertEqual(svc.send_connection_request("diya", "aarav"), "pending")
            self.assertEqual(svc.send_connection_request("aarav", "diya"), "auto_accepted")

            # Already connected error
            with self.assertRaises(ConnectionRuleError):
                svc.send_connection_request("aarav", "diya")

            # Build edges: aarav-rohan, diya-meera, rohan-meera, meera-kabir, kabir-vikram; ananya-sneha
            edges = [
                ("aarav", "rohan"),
                ("diya", "meera"),
                ("rohan", "meera"),
                ("meera", "kabir"),
                ("kabir", "vikram"),
                ("ananya", "sneha"),
            ]
            for u, v in edges:
                svc.send_connection_request(u, v)
                svc.accept_connection_request(v, u)

            # Authorization checks on pending request
            svc.send_connection_request("aarav", "ananya")
            with self.assertRaises(AuthorizationError):
                svc.accept_connection_request("aarav", "ananya")
            with self.assertRaises(AuthorizationError):
                svc.cancel_connection_request("ananya", "aarav")
            svc.cancel_connection_request("aarav", "ananya")

            # 4. Mutual connections, degrees (1st, 2nd, 3rd, 3+, Not connected), and shortest chain
            self.assertEqual([u.username for u in svc.get_mutual_connections("aarav", "meera")], ["diya", "rohan"])
            self.assertEqual(svc.get_degree_and_chain("aarav", "diya").label, "1st")
            self.assertEqual(svc.get_degree_and_chain("aarav", "meera").label, "2nd")
            self.assertEqual(svc.get_degree_and_chain("aarav", "kabir").label, "3rd")
            deg4 = svc.get_degree_and_chain("aarav", "vikram")
            self.assertEqual((deg4.distance, deg4.label), (4, "3+"))
            self.assertEqual(deg4.path, ["aarav", "diya", "meera", "kabir", "vikram"])
            self.assertEqual(svc.get_degree_and_chain("aarav", "ananya").label, "Not connected")

            # 5. People You May Know (meera has 2 mutuals: diya, rohan)
            recs = svc.get_people_you_may_know("aarav", k=3)
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0].username, "meera")
            self.assertEqual(recs[0].mutual_count, 2)
            # N(aarav)={diya, rohan}, N(meera)={diya, kabir, rohan} -> J = 2/3
            self.assertAlmostEqual(recs[0].jaccard_score, 2 / 3, places=4)

            # 6. Posts, Feed k-way merge + paging, Likes, Threaded Comments, Trending
            p_diya_1 = svc.create_post("diya", "Started building a custom Transformer tokenizer.")
            p_rohan_1 = svc.create_post("rohan", "Autonomous rover SLAM demo at Chanakya robotics lab!")
            p_diya_2 = svc.create_post("diya", "Updated tokenizer benchmarks: 2.4x faster.")
            p_aarav = svc.create_post("aarav", "My own post (viewable on profile, deletable).")

            # Only author can delete their post
            with self.assertRaises(AuthorizationError):
                svc.delete_post("diya", p_aarav.post_id)

            page1, more1 = svc.get_home_feed("aarav", limit=2, offset=0)
            self.assertTrue(more1)
            self.assertEqual([p.post_id for p in page1], [p_diya_2.post_id, p_rohan_1.post_id])
            page2, more2 = svc.get_home_feed("aarav", limit=2, offset=2)
            self.assertFalse(more2)
            self.assertEqual([p.post_id for p in page2], [p_diya_1.post_id])

            # Engage on Rohan's post so it tops Trending (score = 1 like + 2*2 comments = 5)
            svc.like_post(p_rohan_1.post_id, "aarav")
            c_top = svc.add_comment(p_rohan_1.post_id, "aarav", "Can I join the lab test?")
            svc.add_comment(p_rohan_1.post_id, "rohan", "Yes! Friday 4 PM.", parent_comment_id=c_top.comment_id)
            svc.like_post(p_diya_2.post_id, "aarav")  # score = 1

            trending = svc.get_trending_posts("aarav", k=3)
            self.assertEqual(trending[0].post.post_id, p_rohan_1.post_id)
            self.assertEqual(trending[0].score, 5)
            self.assertEqual(trending[1].post.post_id, p_diya_2.post_id)
            self.assertEqual(trending[1].score, 1)

            # 7. Notifications unread count & mark-all-read
            self.assertGreater(svc.get_unread_notification_count("aarav"), 0)
            svc.mark_all_notifications_read("aarav")
            self.assertEqual(svc.get_unread_notification_count("aarav"), 0)

            # 8. Communities (iterative DFS with Stack)
            comms = svc.get_all_communities()
            self.assertEqual([c.size for c in comms], [6, 2])
            self.assertEqual(svc.get_user_community("aarav").size, 6)
            self.assertEqual(svc.get_user_community("ananya").size, 2)

            # 9. Search (Trie) & Browse All Students (AVL Tree)
            self.assertEqual([u.username for u in svc.search_users("ver")], ["rohan"])
            all_students = svc.browse_all_students()
            self.assertEqual(
                [u.full_name for u in all_students],
                sorted([u.full_name for u in all_students]),
            )

            # 10. Delete own post, logout, and verify persistence across restart
            svc.delete_post("aarav", p_aarav.post_id)
            self.assertEqual(svc.get_user_posts("aarav"), [])
            svc.logout("aarav")
            self.assertFalse(svc.is_logged_in("aarav"))
            svc.close()

            svc_restarted = CUConnectService(db_path, clock=clock)
            try:
                self.assertEqual(len(svc_restarted.browse_all_students()), 8)
                self.assertEqual(svc_restarted.get_user_posts("aarav"), [])
                self.assertEqual(svc_restarted.get_trending_posts("aarav", k=1)[0].post.post_id, p_rohan_1.post_id)
                self.assertEqual(svc_restarted.get_unread_notification_count("aarav"), 0)
            finally:
                svc_restarted.close()


if __name__ == "__main__":
    unittest.main()
