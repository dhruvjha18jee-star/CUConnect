# tests/test_avl_tree.py
# Unit tests for core.ds.AVLTree covering LL, RR, LR, RL rotations and random stress tests.

import random
import unittest

from core.ds.avl_tree import AVLTree


class TestAVLTree(unittest.TestCase):
    def test_ll_rotation(self) -> None:
        tree = AVLTree()
        for k in [30, 20, 10]:
            tree.insert(k, f"v{k}")
        self.assertTrue(tree.is_balanced())
        self.assertEqual(tree.height(), 2)
        self.assertEqual(tree.inorder(), ["v10", "v20", "v30"])

    def test_rr_rotation(self) -> None:
        tree = AVLTree()
        for k in [10, 20, 30]:
            tree.insert(k, f"v{k}")
        self.assertTrue(tree.is_balanced())
        self.assertEqual(tree.height(), 2)
        self.assertEqual(tree.inorder(), ["v10", "v20", "v30"])

    def test_lr_rotation(self) -> None:
        tree = AVLTree()
        for k in [30, 10, 20]:
            tree.insert(k, f"v{k}")
        self.assertTrue(tree.is_balanced())
        self.assertEqual(tree.height(), 2)
        self.assertEqual(tree.inorder(), ["v10", "v20", "v30"])

    def test_rl_rotation(self) -> None:
        tree = AVLTree()
        for k in [10, 30, 20]:
            tree.insert(k, f"v{k}")
        self.assertTrue(tree.is_balanced())
        self.assertEqual(tree.height(), 2)
        self.assertEqual(tree.inorder(), ["v10", "v20", "v30"])

    def test_ascending_insertions_stay_logarithmic(self) -> None:
        tree = AVLTree()
        for i in range(63):
            tree.insert(i, i)
            self.assertTrue(tree.is_balanced())
        self.assertEqual(len(tree), 63)
        self.assertLessEqual(tree.height(), 7)
        self.assertEqual(tree.inorder(), list(range(63)))

    def test_randomized_insert_update_delete_crosscheck(self) -> None:
        rng = random.Random(2026)
        tree = AVLTree()
        ref: dict[int, str] = {}

        for _ in range(400):
            key = rng.randint(1, 80)
            op = rng.choice(["insert", "insert", "delete", "search"])
            if op == "insert":
                val = f"val_{key}_{rng.randint(1, 9)}"
                tree.insert(key, val)
                ref[key] = val
            elif op == "delete":
                deleted = tree.delete(key)
                self.assertEqual(deleted, key in ref)
                ref.pop(key, None)
            else:
                self.assertEqual(tree.search(key), ref.get(key))

            self.assertEqual(len(tree), len(ref))
            self.assertTrue(tree.is_balanced())

        expected_inorder = [ref[k] for k in sorted(ref.keys())]
        self.assertEqual(tree.inorder(), expected_inorder)


if __name__ == "__main__":
    unittest.main()
