# tests/test_trie.py
# Unit tests and randomized cross-check for core.ds.Trie against linear prefix filtering.

import random
import string
import unittest

from core.ds.trie import Trie


class TestTrie(unittest.TestCase):
    def test_insert_prefix_search_and_remove(self) -> None:
        trie = Trie()
        trie.insert("aarav", "aarav")
        trie.insert("Aarav", "aarav")
        trie.insert("sharma", "aarav")
        trie.insert("aanya", "aanya")
        trie.insert("rohan", "rohan")

        self.assertEqual(trie.prefix_search("aa"), ["aanya", "aarav"])
        self.assertEqual(trie.prefix_search("AA"), ["aanya", "aarav"])
        self.assertEqual(trie.prefix_search("aa", limit=1), ["aanya"])
        self.assertEqual(trie.prefix_search("sha"), ["aarav"])
        self.assertEqual(trie.prefix_search("z"), [])
        self.assertEqual(trie.prefix_search(""), [])

        self.assertTrue(trie.remove("aarav", "aarav"))
        self.assertFalse(trie.remove("aarav", "aarav"))
        self.assertEqual(trie.prefix_search("aa"), ["aanya"])
        # 'sharma' still points to 'aarav' until removed too.
        self.assertEqual(trie.prefix_search("sha"), ["aarav"])

    def test_randomized_crosscheck_against_linear_filter(self) -> None:
        rng = random.Random(7)
        trie = Trie()
        # Reference mapping: word -> set of user_ids
        ref: dict[str, set[str]] = {}
        alphabet = "abcdef"

        for i in range(150):
            word = "".join(rng.choices(alphabet, k=rng.randint(1, 6)))
            uid = f"u{rng.randint(1, 40)}"
            trie.insert(word, uid)
            ref.setdefault(word, set()).add(uid)

        # Remove a subset of entries.
        pairs = [(w, u) for w, us in ref.items() for u in us]
        rng.shuffle(pairs)
        for word, uid in pairs[:40]:
            self.assertTrue(trie.remove(word, uid))
            ref[word].remove(uid)
            if not ref[word]:
                del ref[word]

        # Cross-check 100 random prefixes.
        for _ in range(100):
            prefix = "".join(rng.choices(alphabet, k=rng.randint(1, 4)))
            expected = sorted({u for w, us in ref.items() if w.startswith(prefix) for u in us})
            self.assertEqual(trie.prefix_search(prefix), expected)


if __name__ == "__main__":
    unittest.main()
