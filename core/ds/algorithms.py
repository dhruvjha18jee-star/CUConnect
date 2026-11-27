# core/ds/algorithms.py
# Hand-written Merge Sort and Binary Search for deterministic sorted listings.
# Course mapping: Session 12: Searching Algorithms & Session 14: Sorting Algorithms 2.

from typing import Any, Callable


def _merge(
    left: list[Any],
    right: list[Any],
    key_fn: Callable[[Any], Any],
    reverse: bool,
) -> list[Any]:
    """Merge two already-sorted lists into one sorted list while preserving stability."""
    merged: list[Any] = []
    i = 0
    j = 0
    len_left = len(left)
    len_right = len(right)

    while i < len_left and j < len_right:
        left_key = key_fn(left[i])
        right_key = key_fn(right[j])

        # Using `<=` (or `>=` when reversed) preserves original order on equal keys
        # so merge_sort is guaranteed stable.
        if (not reverse and left_key <= right_key) or (reverse and left_key >= right_key):
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    while i < len_left:
        merged.append(left[i])
        i += 1

    while j < len_right:
        merged.append(right[j])
        j += 1

    return merged


def merge_sort(
    items: list[Any],
    key: Callable[[Any], Any] | None = None,
    reverse: bool = False,
) -> list[Any]:
    """Return a new list containing `items` sorted using divide-and-conquer Merge Sort.

    Why Merge Sort instead of Quick Sort:
    - Guaranteed O(n log n) even on already-sorted or reverse-sorted data.
    - Stable: items with equal keys keep their relative input order.

    Time: O(n log n)
    Space: O(n)
    """
    n = len(items)
    if n <= 1:
        return list(items)

    key_fn = key if key is not None else (lambda x: x)
    mid = n // 2
    left_sorted = merge_sort(items[:mid], key=key_fn, reverse=reverse)
    right_sorted = merge_sort(items[mid:], key=key_fn, reverse=reverse)
    return _merge(left_sorted, right_sorted, key_fn, reverse)


def binary_search(
    sorted_items: list[Any],
    target: Any,
    key: Callable[[Any], Any] | None = None,
) -> int:
    """Search for `target` inside an ascending-sorted list using Binary Search.

    Returns the index of `target` if found, or -1 if absent.
    When `key` is provided, compares `key(sorted_items[mid])` against `target`.

    Time: O(log n)
    Space: O(1)
    """
    key_fn = key if key is not None else (lambda x: x)
    low = 0
    high = len(sorted_items) - 1

    while low <= high:
        mid = low + (high - low) // 2
        mid_val = key_fn(sorted_items[mid])
        if mid_val == target:
            return mid
        if mid_val < target:
            low = mid + 1
        else:
            high = mid - 1

    return -1
