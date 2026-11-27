# tests/test_queue_ds.py
# Unit tests for core.ds.Queue including FIFO order and out-of-order remove_value.

import unittest

from core.ds.queue_ds import Queue


class TestQueue(unittest.TestCase):
    def test_fifo_enqueue_peek_dequeue(self) -> None:
        q = Queue()
        self.assertTrue(q.is_empty())
        self.assertEqual(len(q), 0)

        with self.assertRaises(IndexError):
            q.dequeue()
        with self.assertRaises(IndexError):
            q.peek()

        q.enqueue("a")
        q.enqueue("b")
        q.enqueue("c")
        self.assertEqual(len(q), 3)
        self.assertEqual(q.peek(), "a")
        self.assertEqual(q.to_list(), ["a", "b", "c"])

        self.assertEqual(q.dequeue(), "a")
        self.assertEqual(q.dequeue(), "b")
        self.assertEqual(q.dequeue(), "c")
        self.assertTrue(q.is_empty())

        # Ensure tail pointer reset cleanly by enqueueing again after emptying.
        q.enqueue("d")
        self.assertEqual(q.peek(), "d")
        self.assertEqual(q.dequeue(), "d")

    def test_remove_value_head_middle_tail(self) -> None:
        q = Queue()
        for item in ["req1", "req2", "req3", "req4"]:
            q.enqueue(item)

        self.assertTrue(q.remove_value("req3"))  # middle
        self.assertEqual(q.to_list(), ["req1", "req2", "req4"])
        self.assertTrue(q.remove_value("req4"))  # tail
        self.assertEqual(q.to_list(), ["req1", "req2"])
        # Enqueue after removing tail verifies tail pointer was updated!
        q.enqueue("req5")
        self.assertEqual(q.to_list(), ["req1", "req2", "req5"])
        self.assertTrue(q.remove_value("req1"))  # head
        self.assertEqual(q.to_list(), ["req2", "req5"])
        self.assertFalse(q.remove_value("missing"))
        self.assertEqual(len(q), 2)

    def test_remove_where(self) -> None:
        q = Queue()
        q.enqueue(("alice", "bob"))
        q.enqueue(("carol", "bob"))
        removed = q.remove_where(lambda pair: pair[0] == "carol")
        self.assertEqual(removed, ("carol", "bob"))
        self.assertEqual(q.to_list(), [("alice", "bob")])


if __name__ == "__main__":
    unittest.main()
