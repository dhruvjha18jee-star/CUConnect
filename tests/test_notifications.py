# tests/test_notifications.py
# Unit tests for core.notifications.NotificationManager (per-user Queue).

import unittest

from core.models import ResourceNotFoundError
from core.notifications import NotificationManager


class TestNotificationManager(unittest.TestCase):
    def test_notify_unread_count_and_mark_read(self) -> None:
        nm = NotificationManager()
        nm.register_user("aarav")

        n1 = nm.notify("aarav", "diya", "connection_request", "Diya sent a request", 10.0, 1)
        n2 = nm.notify("aarav", "rohan", "post_like", "Rohan liked your post", 20.0, 2)

        self.assertEqual(nm.unread_count("aarav"), 2)
        all_notifs = nm.get_notifications("aarav")
        self.assertEqual([n.notification_id for n in all_notifs], [n2.notification_id, n1.notification_id])

        nm.mark_read("aarav", n1.notification_id)
        self.assertEqual(nm.unread_count("aarav"), 1)
        self.assertEqual(len(nm.get_notifications("aarav", unread_only=True)), 1)

        marked = nm.mark_all_read("aarav")
        self.assertEqual(marked, [n2.notification_id])
        self.assertEqual(nm.unread_count("aarav"), 0)

        with self.assertRaises(ResourceNotFoundError):
            nm.mark_read("aarav", "nonexistent")


if __name__ == "__main__":
    unittest.main()
