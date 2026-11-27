# tests/test_heap.py
# Unit tests and randomized cross-check for core.ds.MinHeap against Python sorted().

import random
import unittest

from core.ds.heap import MinHeap


class TestMinHeap(unittest.TestCase):
    def test_basic_min_and_max_heap(self) -> None:
        min_h = MinHeap()
        for val in [7, 2, 9, 1, 5, 2]:
            min_h.push(val)
        self.assertEqual(len(min_h), 6)
        self.assertEqual(min_h.peek(), 1)
        popped = [min_h.pop() for _ in range(len(min_h))]
        self.assertEqual(popped, [1, 2, 2, 5, 7, 9])

        # Max-heap via negated key function.
        max_h = MinHeap(key=lambda x: -x)
        for val in [7, 2, 9, 1, 5]:
            max_h.push(val)
        popped_max = [max_h.pop() for _ in range(len(max_h))]
        self.assertEqual(popped_max, [9, 7, 5, 2, 1])

    def test_empty_errors(self) -> None:
        h = MinHeap()
        with self.assertRaises(IndexError):
            h.pop()
        with self.assertRaises(IndexError):
            h.peek()

    def test_deterministic_tie_breaking_non_comparable_items(self) -> None:
        h = MinHeap(key=lambda item: item["score"])
        h.push({"id": "first", "score": 10})
        h.push({"id": "second", "score": 10})
        h.push({"id": "third", "score": 5})

        self.assertEqual(h.pop()["id"], "third")
        self.assertEqual(h.pop()["id"], "first")
        self.assertEqual(h.pop()["id"], "second")

    def test_randomized_crosscheck_against_sorted(self) -> None:
        rng = random.Random(123)
        for _ in range(25):
            nums = [rng.randint(-500, 500) for _ in range(rng.randint(0, 150))]
            h = MinHeap()
            for n in nums:
                h.push(n)
            result = []
            while not h.is_empty():
                result.append(h.pop())
            self.assertEqual(result, sorted(nums))


if __name__ == "__main__":
    unittest.main()
