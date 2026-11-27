# core/ds/heap.py
# Hand-written Array-Based Binary Min-Heap with key function (supports Max-Heap).
# Course mapping: Session 15: Heaps and Hash Tables & Session 7: Priority Queues.

from typing import Any, Callable


class MinHeap:
    """Array-based binary min-heap supporting a custom key function.

    Passing a negated key (for example `key=lambda post: -post.created_at`) turns
    this MinHeap into a Max-Heap without duplicating heap code.

    Deterministic tie-breaking:
    Each entry stores `(priority_key, insertion_seq, item)`. When two items have
    equal priority keys, the earlier-inserted item wins and Python never attempts
    to compare the raw `item` objects (which may not define `<`).
    """

    def __init__(self, key: Callable[[Any], Any] | None = None) -> None:
        """Create an empty MinHeap with an optional key function.

        Time: O(1)
        Space: O(1)
        """
        self._data: list[tuple[Any, int, Any]] = []
        self._key_fn: Callable[[Any], Any] = key if key is not None else (lambda x: x)
        self._counter: int = 0

    def _sift_up(self, index: int) -> None:
        """Restore heap order by moving the element at `index` upward."""
        while index > 0:
            parent = (index - 1) // 2
            if self._data[index] < self._data[parent]:
                self._data[index], self._data[parent] = self._data[parent], self._data[index]
                index = parent
            else:
                break

    def _sift_down(self, index: int) -> None:
        """Restore heap order by moving the element at `index` downward."""
        size = len(self._data)
        while True:
            left = 2 * index + 1
            right = 2 * index + 2
            smallest = index

            if left < size and self._data[left] < self._data[smallest]:
                smallest = left
            if right < size and self._data[right] < self._data[smallest]:
                smallest = right

            if smallest == index:
                break

            self._data[index], self._data[smallest] = self._data[smallest], self._data[index]
            index = smallest

    def push(self, item: Any) -> None:
        """Insert `item` into the heap and restore the min-heap invariant.

        Time: O(log n)
        Space: O(1)
        """
        priority = self._key_fn(item)
        entry = (priority, self._counter, item)
        self._counter += 1
        self._data.append(entry)
        self._sift_up(len(self._data) - 1)

    def pop(self) -> Any:
        """Remove and return the item with the smallest priority key.

        Raises IndexError if the heap is empty.

        Time: O(log n)
        Space: O(1)
        """
        if not self._data:
            raise IndexError("Cannot pop from an empty heap.")

        min_item = self._data[0][2]
        last_entry = self._data.pop()

        if self._data:
            # Move the last leaf to the root and sift it down to its proper spot.
            self._data[0] = last_entry
            self._sift_down(0)

        return min_item

    def peek(self) -> Any:
        """Return the smallest item without removing it.

        Raises IndexError if the heap is empty.

        Time: O(1)
        Space: O(1)
        """
        if not self._data:
            raise IndexError("Cannot peek at an empty heap.")
        return self._data[0][2]

    def is_empty(self) -> bool:
        """Return True if the heap has no items.

        Time: O(1)
        Space: O(1)
        """
        return len(self._data) == 0

    def __len__(self) -> int:
        """Return the number of items stored in the heap.

        Time: O(1)
        Space: O(1)
        """
        return len(self._data)
