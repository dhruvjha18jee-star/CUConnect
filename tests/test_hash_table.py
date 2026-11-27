# tests/test_hash_table.py
# Unit tests and randomized cross-check for core.ds.HashTable against Python dict.

import random
import string
import unittest

from core.ds.hash_table import HashTable


class TestHashTable(unittest.TestCase):
    def test_put_get_update_remove_and_len(self) -> None:
        ht = HashTable(initial_capacity=4)
        self.assertEqual(len(ht), 0)
        self.assertFalse(ht.contains("aarav"))
        self.assertIsNone(ht.get("aarav"))
        self.assertEqual(ht.get("aarav", "fallback"), "fallback")

        ht.put("aarav", 101)
        ht.put("diya", 202)
        self.assertEqual(len(ht), 2)
        self.assertTrue(ht.contains("aarav"))
        self.assertEqual(ht.get("aarav"), 101)
        self.assertEqual(ht.get("diya"), 202)

        # Updating existing key must not grow size.
        ht.put("aarav", 999)
        self.assertEqual(len(ht), 2)
        self.assertEqual(ht.get("aarav"), 999)

        removed = ht.remove("aarav")
        self.assertEqual(removed, 999)
        self.assertEqual(len(ht), 1)
        self.assertFalse(ht.contains("aarav"))

        with self.assertRaises(KeyError):
            ht.remove("nonexistent")

    def test_resize_triggers_above_load_factor_075(self) -> None:
        ht = HashTable(initial_capacity=8)
        self.assertEqual(ht.capacity(), 8)
        # 6 items -> load factor 6/8 = 0.75 (not strictly > 0.75).
        for i in range(6):
            ht.put(f"user_{i}", i)
        self.assertEqual(ht.capacity(), 8)
        # 7th item -> load factor 7/8 = 0.875 > 0.75 -> doubles to 16.
        ht.put("user_6", 6)
        self.assertEqual(ht.capacity(), 16)
        for i in range(7):
            self.assertEqual(ht.get(f"user_{i}"), i)

    def test_anagrams_hash_differently(self) -> None:
        ht = HashTable()
        self.assertNotEqual(ht._polynomial_hash("abc"), ht._polynomial_hash("cba"))
        ht.put("abc", 1)
        ht.put("cba", 2)
        self.assertEqual(ht.get("abc"), 1)
        self.assertEqual(ht.get("cba"), 2)

    def test_randomized_crosscheck_against_dict(self) -> None:
        rng = random.Random(42)
        ht = HashTable(initial_capacity=4)
        ref: dict[str, int] = {}
        key_pool = [
            "".join(rng.choices(string.ascii_lowercase, k=rng.randint(1, 8)))
            for _ in range(120)
        ]

        for step in range(800):
            key = rng.choice(key_pool)
            op = rng.choice(["put", "put", "get", "remove", "contains"])
            if op == "put":
                val = rng.randint(-1000, 1000)
                ht.put(key, val)
                ref[key] = val
            elif op == "get":
                self.assertEqual(ht.get(key), ref.get(key))
            elif op == "contains":
                self.assertEqual(ht.contains(key), key in ref)
            elif op == "remove":
                if key in ref:
                    self.assertEqual(ht.remove(key), ref.pop(key))
                else:
                    with self.assertRaises(KeyError):
                        ht.remove(key)

            self.assertEqual(len(ht), len(ref))
            self.assertLessEqual(ht.load_factor(), HashTable.LOAD_FACTOR_THRESHOLD)

        self.assertEqual(set(ht.keys()), set(ref.keys()))
        self.assertEqual(sorted(ht.values()), sorted(ref.values()))
        self.assertEqual(set(ht.items()), set(ref.items()))


if __name__ == "__main__":
    unittest.main()
