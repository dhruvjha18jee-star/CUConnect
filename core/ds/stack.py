# core/ds/stack.py
# Hand-written LIFO Stack backed by linked nodes for undo, navigation, and DFS.
# Course mapping: Session 6: Stacks.

from typing import Any


class _StackNode:
    """Internal node linking each pushed value to the item below it."""

    def __init__(self, value: Any, below: "_StackNode | None" = None) -> None:
        self.value = value
        self.below = below


class Stack:
    """Last-In-First-Out (LIFO) Stack with strict O(1) push, pop, and peek.

    Used in CUConnect for:
    - Engine undo history (reversing the most recent send-request or remove-connection).
    - Console menu back-navigation (returning to the previous screen).
    - Iterative DFS traversal when detecting connected components (communities).
    """

    def __init__(self) -> None:
        """Create an empty stack.

        Time: O(1)
        Space: O(1)
        """
        self._top: _StackNode | None = None
        self._size: int = 0

    def push(self, value: Any) -> None:
        """Push `value` onto the top of the stack.

        Time: O(1)
        Space: O(1)
        """
        self._top = _StackNode(value, self._top)
        self._size += 1

    def pop(self) -> Any:
        """Remove and return the value on top of the stack.

        Raises IndexError if the stack is empty.

        Time: O(1)
        Space: O(1)
        """
        if self._top is None:
            raise IndexError("Cannot pop from an empty stack.")
        value = self._top.value
        self._top = self._top.below
        self._size -= 1
        return value

    def peek(self) -> Any:
        """Return the top value without removing it.

        Raises IndexError if the stack is empty.

        Time: O(1)
        Space: O(1)
        """
        if self._top is None:
            raise IndexError("Cannot peek at an empty stack.")
        return self._top.value

    def is_empty(self) -> bool:
        """Return True if the stack contains no items.

        Time: O(1)
        Space: O(1)
        """
        return self._top is None

    def clear(self) -> None:
        """Remove all items from the stack.

        Time: O(1)
        Space: O(1)
        """
        self._top = None
        self._size = 0

    def to_list(self) -> list[Any]:
        """Return items from top to bottom as a list without modifying the stack.

        Time: O(n)
        Space: O(n)
        """
        items: list[Any] = []
        current = self._top
        while current is not None:
            items.append(current.value)
            current = current.below
        return items

    def __len__(self) -> int:
        """Return the number of items currently on the stack.

        Time: O(1)
        Space: O(1)
        """
        return self._size
