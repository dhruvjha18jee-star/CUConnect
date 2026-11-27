# tests/test_algorithms.py
# Unit tests for core.ds.algorithms (merge_sort and binary_search).

import random
import unittest

from core.ds.algorithms import binary_search, merge_sort


class TestAlgorithms(unittest.TestCase):
    def test_merge_sort_numbers_and_stability(self) -> None:
        self.assertEqual(merge_sort([]), [])
        self.assertEqual(merge_sort([42]), [42])
        self.assertEqual(merge_sort([5, 1, 4, 2, 8, 2]), [1, 2, 2, 4, 5, 8])
        self.assertEqual(merge_sort([5, 1, 4, 2, 8], reverse=True), [8, 5, 4, 2, 1])

        # Verify stability on equal keys.
        records = [("a", 2), ("b", 1), ("c", 2), ("d", 1), ("e", 2)]
        sorted_records = merge_sort(records, key=lambda pair: pair[1])
        self.assertEqual(sorted_records, [("b", 1), ("d", 1), ("a", 2), ("c", 2), ("e", 2)])

    def test_merge_sort_randomized(self) -> None:
        rng = random.Random(99)
        for _ in range(20):
            data = [rng.randint(-1000, 1000) for _ in range(rng.randint(0, 100))]
            self.assertEqual(merge_sort(data), sorted(data))
            self.assertEqual(merge_sort(data, reverse=True), sorted(data, reverse=True))

    def test_binary_search(self) -> None:
        arr = ["aarav", "diya", "kabir", "meera", "rohan"]
        self.assertEqual(binary_search(arr, "aarav"), 0)
        self.assertEqual(binary_search(arr, "kabir"), 2)
        self.assertEqual(binary_search(arr, "rohan"), 4)
        self.assertEqual(binary_search(arr, "vikram"), -1)
        self.assertEqual(binary_search([], "aarav"), -1)

        objs = [{"name": n} for n in arr]
        self.assertEqual(binary_search(objs, "meera", key=lambda x: x["name"]), 3)


if __name__ == "__main__":
    unittest.main()
