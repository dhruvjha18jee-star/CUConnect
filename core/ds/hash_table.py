# core/ds/hash_table.py
# Hand-written Hash Table using separate chaining and a polynomial rolling hash.
# Course mapping: Session 15: Heaps and Hash Tables (and Session 4: Singly Linked Lists).

from typing import Any, Iterator


class _ChainNode:
    """Single key-value node stored inside a hash bucket's linked chain."""

    def __init__(self, key: Any, value: Any, next_node: "_ChainNode | None" = None) -> None:
        self.key = key
        self.value = value
        self.next = next_node


class HashTable:
    """Hash table with separate chaining and automatic rehashing at load factor > 0.75.

    Why separate chaining instead of open addressing:
    - Deletions (removing users, unliking posts, cancelling edges) are trivial and
      do not require tombstone markers that degrade probe sequences over time.
    - Bucket chains stay very short (O(1) average) as long as we resize whenever
      the load factor (size / capacity) exceeds 0.75.
    """

    LOAD_FACTOR_THRESHOLD = 0.75
    HASH_BASE = 31
    HASH_MOD = 1_000_000_007

    def __init__(self, initial_capacity: int = 16) -> None:
        """Create an empty hash table with at least 4 buckets.

        Time: O(capacity)
        Space: O(capacity)
        """
        if initial_capacity < 4:
            initial_capacity = 4
        self._capacity: int = initial_capacity
        self._buckets: list[_ChainNode | None] = [None] * self._capacity
        self._size: int = 0

    def _polynomial_hash(self, key: Any) -> int:
        """Compute a deterministic hash code without calling Python's built-in hash().

        For strings we use a polynomial rolling hash:
            h = (h * 31 + ord(ch)) % 1_000_000_007
        Using a prime base (31) spreads anagrams like 'abc' and 'cba' into
        different buckets because character position changes the power of 31.
        """
        if isinstance(key, int) and not isinstance(key, bool):
            # Map negative and positive integers cleanly into [0, HASH_MOD).
            return abs(key) % self.HASH_MOD

        text = key if isinstance(key, str) else str(key)
        hash_value = 0
        for ch in text:
            hash_value = (hash_value * self.HASH_BASE + ord(ch)) % self.HASH_MOD
        return hash_value

    def _bucket_index(self, key: Any, capacity: int) -> int:
        """Compress the hash code into a valid bucket index in [0, capacity)."""
        return self._polynomial_hash(key) % capacity

    def _resize(self, new_capacity: int) -> None:
        """Allocate a larger bucket array and rehash every existing key-value pair.

        Why rehash instead of copying buckets directly:
        Bucket indices depend on `capacity`, so changing `capacity` changes
        which bucket each key belongs to.
        """
        new_buckets: list[_ChainNode | None] = [None] * new_capacity

        for head in self._buckets:
            current = head
            while current is not None:
                next_node = current.next
                index = self._bucket_index(current.key, new_capacity)
                # Insert at head of the new bucket chain in O(1).
                current.next = new_buckets[index]
                new_buckets[index] = current
                current = next_node

        self._buckets = new_buckets
        self._capacity = new_capacity

    def load_factor(self) -> float:
        """Return the current load factor (number of entries / number of buckets).

        Time: O(1)
        Space: O(1)
        """
        return self._size / self._capacity

    def capacity(self) -> int:
        """Return the current number of buckets allocated in the table.

        Time: O(1)
        Space: O(1)
        """
        return self._capacity

    def put(self, key: Any, value: Any) -> None:
        """Insert a new key-value pair or overwrite the value if the key exists.

        Triggers a 2x resize and rehash whenever inserting would push the load
        factor strictly above 0.75.

        Time: O(1) amortized average, O(n) worst case (on resize or all keys colliding)
        Space: O(1) amortized, O(n) when resizing
        """
        index = self._bucket_index(key, self._capacity)
        current = self._buckets[index]

        # First check whether the key already exists so we update in place.
        while current is not None:
            if current.key == key:
                current.value = value
                return
            current = current.next

        # Key is new: prepend a new chain node to this bucket.
        new_node = _ChainNode(key, value, self._buckets[index])
        self._buckets[index] = new_node
        self._size += 1

        if self.load_factor() > self.LOAD_FACTOR_THRESHOLD:
            self._resize(self._capacity * 2)

    def get(self, key: Any, default: Any = None) -> Any:
        """Return the value stored for `key`, or `default` if the key is absent.

        Time: O(1) average, O(n) worst case
        Space: O(1)
        """
        index = self._bucket_index(key, self._capacity)
        current = self._buckets[index]
        while current is not None:
            if current.key == key:
                return current.value
            current = current.next
        return default

    def remove(self, key: Any) -> Any:
        """Delete `key` from the table and return its associated value.

        Raises KeyError if `key` is not present.

        Time: O(1) average, O(n) worst case
        Space: O(1)
        """
        index = self._bucket_index(key, self._capacity)
        previous: _ChainNode | None = None
        current = self._buckets[index]

        while current is not None:
            if current.key == key:
                if previous is None:
                    self._buckets[index] = current.next
                else:
                    previous.next = current.next
                self._size -= 1
                return current.value
            previous = current
            current = current.next

        raise KeyError(key)

    def contains(self, key: Any) -> bool:
        """Return True if `key` is stored in the table, False otherwise.

        Time: O(1) average, O(n) worst case
        Space: O(1)
        """
        index = self._bucket_index(key, self._capacity)
        current = self._buckets[index]
        while current is not None:
            if current.key == key:
                return True
            current = current.next
        return False

    def keys(self) -> list[Any]:
        """Return a list containing all keys currently stored in the table.

        Time: O(n + capacity)
        Space: O(n)
        """
        result: list[Any] = []
        for head in self._buckets:
            current = head
            while current is not None:
                result.append(current.key)
                current = current.next
        return result

    def values(self) -> list[Any]:
        """Return a list containing all values currently stored in the table.

        Time: O(n + capacity)
        Space: O(n)
        """
        result: list[Any] = []
        for head in self._buckets:
            current = head
            while current is not None:
                result.append(current.value)
                current = current.next
        return result

    def items(self) -> list[tuple[Any, Any]]:
        """Return a list of (key, value) pairs stored in the table.

        Time: O(n + capacity)
        Space: O(n)
        """
        result: list[tuple[Any, Any]] = []
        for head in self._buckets:
            current = head
            while current is not None:
                result.append((current.key, current.value))
                current = current.next
        return result

    def __len__(self) -> int:
        """Return the number of key-value pairs stored in the table.

        Time: O(1)
        Space: O(1)
        """
        return self._size

    def __contains__(self, key: Any) -> bool:
        """Support Python's `key in table` syntax by delegating to `contains`.

        Time: O(1) average, O(n) worst case
        Space: O(1)
        """
        return self.contains(key)

    def __iter__(self) -> Iterator[Any]:
        """Iterate over all keys stored in the table.

        Time: O(n + capacity)
        Space: O(1)
        """
        for head in self._buckets:
            current = head
            while current is not None:
                yield current.key
                current = current.next
