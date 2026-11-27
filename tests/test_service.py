# tests/test_service.py
# Unit tests for core.service.CUConnectService facade (undo stack, AVL browse, notifications, restart).

import os
import tempfile
import unittest

from core.models import AuthError, AuthorizationError, ConnectionRuleError, ValidationError
from core.service import CUConnectService, ScreenNavigator


class FakeClock:
    def __init__(self, start: float = 1_700_000_000.0) -> None:
        self.t = start

    def __call__(self) -> float:
        self.t += 10.0
        return self.t


class TestCUConnectService(unittest.TestCase):
    def test_undo_send_request_and_remove_connection(self) -> None:
        clock = FakeClock()
        svc = CUConnectService(":memory:", clock=clock)
        try:
            svc.sign_up("aarav", "pass1234", "Aarav Sharma", "CSAI", 2)
            svc.sign_up("diya", "pass1234", "Diya Nair", "EVE", 2)

            # Send request and undo it
            status = svc.send_connection_request("aarav", "diya")
            self.assertEqual(status, "pending")
            self.assertTrue(svc.can_undo("aarav"))
            msg = svc.undo_last_action("aarav")
            self.assertIn("Undid connection request", msg)
            self.assertEqual(svc.get_outgoing_requests("aarav"), [])
            self.assertEqual(svc.get_incoming_requests("diya"), [])

            # Connect, remove connection, then undo removal
            svc.send_connection_request("aarav", "diya")
            svc.accept_connection_request("diya", "aarav")
            self.assertEqual(svc.get_connection_usernames("aarav"), ["diya"])

            svc.remove_connection("aarav", "diya")
            self.assertEqual(svc.get_connection_usernames("aarav"), [])

            msg2 = svc.undo_last_action("aarav")
            self.assertIn("Restored connection", msg2)
            self.assertEqual(svc.get_connection_usernames("aarav"), ["diya"])
            self.assertEqual(svc.get_connection_usernames("diya"), ["aarav"])

            # Trying to undo the earlier send_request that was already accepted fails cleanly
            with self.assertRaises(ValidationError):
                svc.undo_last_action("aarav")
        finally:
            svc.close()

    def test_avl_directory_and_profile_rename_sync(self) -> None:
        clock = FakeClock()
        svc = CUConnectService(":memory:", clock=clock)
        try:
            svc.sign_up("zara", "pass1234", "Zara Khan", "CSE", 1)
            svc.sign_up("aarav", "pass1234", "Aarav Sharma", "CSAI", 2)
            svc.sign_up("meera", "pass1234", "Meera Iyer", "EECS", 3)

            ordered = [u.username for u in svc.browse_all_students()]
            self.assertEqual(ordered, ["aarav", "meera", "zara"])

            # Rename Zara to Ananya -> AVL tree and Trie update automatically!
            svc.update_profile("zara", full_name="Ananya Rao")
            ordered2 = [u.username for u in svc.browse_all_students()]
            self.assertEqual(ordered2, ["aarav", "zara", "meera"])
            self.assertEqual([u.username for u in svc.search_users("anan")], ["zara"])
            self.assertEqual(svc.search_users("zara"), [svc.get_profile("zara")])  # username still matches
            stats = svc.get_engine_stats()
            self.assertTrue(stats["avl_balanced"])
        finally:
            svc.close()

    def test_full_restart_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "restart_test.db")
            clock = FakeClock()

            svc1 = CUConnectService(db_path, clock=clock)
            svc1.sign_up("aarav", "secret123", "Aarav Sharma", "CSAI", 2, bio="AI", skills=["Python"])
            svc1.sign_up("diya", "secret123", "Diya Nair", "EVE", 2, bio="VLSI", skills=["Verilog"])
            svc1.sign_up("rohan", "secret123", "Rohan Verma", "EECS", 3, bio="Robotics", skills=["C++"])
            svc1.sign_up("meera", "secret123", "Meera Iyer", "CSAI", 3, bio="Systems", skills=["Rust"])

            svc1.send_connection_request("aarav", "diya")
            svc1.accept_connection_request("diya", "aarav")
            svc1.send_connection_request("diya", "rohan")
            svc1.accept_connection_request("rohan", "diya")
            svc1.send_connection_request("aarav", "meera")  # stays pending

            p1 = svc1.create_post("diya", "FPGA accelerator benchmark results")
            svc1.like_post(p1.post_id, "aarav")
            c1 = svc1.add_comment(p1.post_id, "aarav", "Super clean timing!")
            r1 = svc1.add_comment(p1.post_id, "diya", "Thanks Aarav!", parent_comment_id=c1.comment_id)

            unread_before = svc1.get_unread_notification_count("diya")
            svc1.close()

            # Restart engine completely from scratch against the same SQLite file!
            svc2 = CUConnectService(db_path, clock=clock)
            try:
                # Authentication survives restart
                logged = svc2.login("aarav", "secret123")
                self.assertEqual(logged.full_name, "Aarav Sharma")
                with self.assertRaises(AuthError):
                    svc2.login("aarav", "wrongpass")

                # Connections & pending requests survive restart
                self.assertEqual(svc2.get_connection_usernames("aarav"), ["diya"])
                self.assertEqual([r.receiver for r in svc2.get_outgoing_requests("aarav")], ["meera"])
                self.assertEqual([r.sender for r in svc2.get_incoming_requests("meera")], ["aarav"])

                # BFS degree, suggestions, and communities work identically after reload
                deg = svc2.get_degree_and_chain("aarav", "rohan")
                self.assertEqual((deg.distance, deg.label, deg.path), (2, "2nd", ["aarav", "diya", "rohan"]))
                recs = svc2.get_people_you_may_know("aarav")
                self.assertEqual([s.username for s in recs], ["rohan"])

                # Posts, likes, nested comments, trending, and notifications survive restart
                feed, has_more = svc2.get_home_feed("aarav")
                self.assertFalse(has_more)
                self.assertEqual([p.post_id for p in feed], [p1.post_id])
                self.assertEqual(svc2.get_like_count(p1.post_id), 1)
                self.assertTrue(svc2.has_liked(p1.post_id, "aarav"))
                comments = svc2.get_post_comments(p1.post_id)
                self.assertEqual([(c.comment_id, d) for c, d in comments], [(c1.comment_id, 0), (r1.comment_id, 1)])
                self.assertEqual(svc2.get_unread_notification_count("diya"), unread_before)

                # Trie & AVL directory hydrated accurately
                self.assertEqual([u.username for u in svc2.search_users("diy")], ["diya"])
                self.assertEqual(
                    [u.username for u in svc2.browse_all_students()],
                    ["aarav", "diya", "meera", "rohan"],
                )
            finally:
                svc2.close()

    def test_screen_navigator_stack_back_navigation(self) -> None:
        nav = ScreenNavigator("Auth")
        self.assertEqual(nav.current(), "Auth")
        self.assertEqual(nav.back(), "Auth")  # Never pops below root

        nav.reset("Home")
        nav.push("Connections")
        nav.push("Mutuals")
        self.assertEqual(nav.breadcrumb(), "Home > Connections > Mutuals")
        self.assertEqual(nav.back(), "Connections")
        self.assertEqual(nav.back(), "Home")
        self.assertEqual(nav.breadcrumb(), "Home")


if __name__ == "__main__":
    unittest.main()
