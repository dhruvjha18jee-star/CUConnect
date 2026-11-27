# tests/test_repository.py
# Unit tests for storage.repository.SQLiteRepository write-through and reload behavior.

import os
import tempfile
import unittest

from core.models import Comment, ConnectionRequest, Notification, Post, User
from storage.repository import SQLiteRepository


class TestSQLiteRepository(unittest.TestCase):
    def test_save_and_load_all_entities(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "repo_test.db")
            repo = SQLiteRepository(db_path)

            u1 = User("aarav", "hash1", "Aarav Sharma", "CSAI", 2, "Bio 1", ["Python", "DSA"], 10.0)
            u2 = User("diya", "hash2", "Diya Nair", "EVE", 2, "Bio 2", ["Verilog"], 20.0)
            repo.save_user(u1)
            repo.save_user(u2)

            u1.bio = "Updated Bio"
            repo.update_user(u1)

            repo.save_connection("diya", "aarav", 30.0)
            repo.save_request(ConnectionRequest("aarav", "diya", 40.0, 1))
            repo.save_post(Post("p1", "aarav", "Hello CU!", 50.0, 2, "ui/assets/post_rover_demo.png"))
            repo.save_like("p1", "diya", 55.0)
            repo.save_comment(Comment("c1", "p1", "diya", None, "Nice!", 60.0, 3))
            repo.save_notification(
                Notification("n1", "aarav", "diya", "post_like", "Diya liked your post", "p1", 65.0, 4, False)
            )
            repo.mark_notification_read("n1")
            repo.close()

            # Reopen fresh connection to prove disk persistence
            repo2 = SQLiteRepository(db_path)
            users = {u.username: u for u in repo2.load_all_users()}
            self.assertEqual(users["aarav"].bio, "Updated Bio")
            self.assertEqual(users["aarav"].skills, ["Python", "DSA"])
            # Undirected connection stored canonically
            self.assertEqual(repo2.load_all_connections(), [("aarav", "diya")])
            self.assertEqual(len(repo2.load_all_requests()), 1)
            loaded_posts = repo2.load_all_posts()
            self.assertEqual(len(loaded_posts), 1)
            self.assertEqual(loaded_posts[0].image_path, "ui/assets/post_rover_demo.png")
            self.assertEqual(len(repo2.load_all_likes()), 1)
            self.assertEqual(len(repo2.load_all_comments()), 1)
            notifs = repo2.load_all_notifications()
            self.assertEqual(len(notifs), 1)
            self.assertTrue(notifs[0].is_read)

            # Deleting post cascades likes & comments
            repo2.delete_post("p1")
            self.assertEqual(repo2.load_all_posts(), [])
            self.assertEqual(repo2.load_all_likes(), [])
            self.assertEqual(repo2.load_all_comments(), [])
            repo2.close()


if __name__ == "__main__":
    unittest.main()
