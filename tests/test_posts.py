# tests/test_posts.py
# Unit tests for core.posts.PostManager (per-user SinglyLinkedList, newest at head).

import unittest

from core.models import AuthorizationError, ResourceNotFoundError, ValidationError
from core.posts import PostManager


class TestPostManager(unittest.TestCase):
    def setUp(self) -> None:
        self.pm = PostManager()
        self.pm.register_user("aarav")
        self.pm.register_user("diya")

    def test_create_view_and_delete_own_posts(self) -> None:
        with self.assertRaises(ValidationError):
            self.pm.create_post("aarav", "   ", 1.0, 1)

        p1 = self.pm.create_post("aarav", "First project update", 10.0, 1)
        p2 = self.pm.create_post("aarav", "Second project update", 20.0, 2)
        p3 = self.pm.create_post("aarav", "Third project update", 30.0, 3)

        posts = self.pm.get_user_posts("aarav")
        self.assertEqual([p.post_id for p in posts], [p3.post_id, p2.post_id, p1.post_id])

        # Another user cannot delete aarav's post.
        with self.assertRaises(AuthorizationError):
            self.pm.delete_post("diya", p2.post_id)

        deleted = self.pm.delete_post("aarav", p2.post_id)
        self.assertEqual(deleted.post_id, p2.post_id)
        self.assertEqual(
            [p.post_id for p in self.pm.get_user_posts("aarav")],
            [p3.post_id, p1.post_id],
        )

        with self.assertRaises(ResourceNotFoundError):
            self.pm.get_post(p2.post_id)

    def test_create_post_with_optional_image_path(self) -> None:
        p_img = self.pm.create_post(
            "aarav",
            "Rover lab demo",
            40.0,
            4,
            image_path="ui/assets/post_rover_demo.png",
        )
        self.assertEqual(p_img.image_path, "ui/assets/post_rover_demo.png")
        p_blank = self.pm.create_post("aarav", "Text only", 50.0, 5, image_path="   ")
        self.assertIsNone(p_blank.image_path)


if __name__ == "__main__":
    unittest.main()
