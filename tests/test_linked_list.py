# tests/test_linked_list.py
# Unit tests for core.ds.SinglyLinkedList.

import unittest

from core.ds.linked_list import SinglyLinkedList


class TestSinglyLinkedList(unittest.TestCase):
    def test_insert_head_preserves_newest_first(self) -> None:
        ll = SinglyLinkedList()
        self.assertTrue(ll.is_empty())
        self.assertEqual(len(ll), 0)

        ll.insert_head("post1")
        ll.insert_head("post2")
        ll.insert_head("post3")

        self.assertFalse(ll.is_empty())
        self.assertEqual(len(ll), 3)
        self.assertEqual(ll.traverse(), ["post3", "post2", "post1"])
        self.assertEqual(list(ll), ["post3", "post2", "post1"])
        assert ll.head is not None
        self.assertEqual(ll.head.value, "post3")

    def test_delete_value_head_middle_tail_and_missing(self) -> None:
        ll = SinglyLinkedList()
        for v in [1, 2, 3, 4]:
            ll.insert_head(v)
        # Current order: [4, 3, 2, 1]
        self.assertTrue(ll.delete_value(4))  # head
        self.assertEqual(ll.traverse(), [3, 2, 1])
        self.assertTrue(ll.delete_value(2))  # middle
        self.assertEqual(ll.traverse(), [3, 1])
        self.assertTrue(ll.delete_value(1))  # tail
        self.assertEqual(ll.traverse(), [3])
        self.assertFalse(ll.delete_value(99))  # missing
        self.assertTrue(ll.delete_value(3))  # last remaining
        self.assertTrue(ll.is_empty())
        self.assertEqual(len(ll), 0)

    def test_delete_by_id(self) -> None:
        ll = SinglyLinkedList()
        ll.insert_head({"id": "p1", "text": "hello"})
        ll.insert_head({"id": "p2", "text": "world"})
        removed = ll.delete_by_id("p1", lambda item: item["id"])
        self.assertEqual(removed, {"id": "p1", "text": "hello"})
        self.assertEqual(len(ll), 1)
        self.assertIsNone(ll.delete_by_id("p999", lambda item: item["id"]))


if __name__ == "__main__":
    unittest.main()
