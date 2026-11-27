# tests/test_stack.py
# Unit tests for core.ds.Stack.

import unittest

from core.ds.stack import Stack


class TestStack(unittest.TestCase):
    def test_lifo_push_peek_pop_clear(self) -> None:
        s = Stack()
        self.assertTrue(s.is_empty())
        self.assertEqual(len(s), 0)

        with self.assertRaises(IndexError):
            s.pop()
        with self.assertRaises(IndexError):
            s.peek()

        s.push("home")
        s.push("profile")
        s.push("edit")
        self.assertEqual(len(s), 3)
        self.assertEqual(s.peek(), "edit")
        self.assertEqual(s.to_list(), ["edit", "profile", "home"])

        self.assertEqual(s.pop(), "edit")
        self.assertEqual(s.pop(), "profile")
        self.assertEqual(s.peek(), "home")
        s.clear()
        self.assertTrue(s.is_empty())
        self.assertEqual(len(s), 0)


if __name__ == "__main__":
    unittest.main()
