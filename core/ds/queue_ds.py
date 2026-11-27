# core/ds/queue_ds.py
# Hand-written Linked-List-Based Queue with O(1) enqueue/dequeue and remove_value.
# Course mapping: Session 7: Queues (and Session 4: Singly Linked Lists).

from typing import Any, Callable, Iterator


class _QueueNode:
    """Internal node for the linked-list queue."""

    def __init__(self, value: Any, next_node: "_QueueNode | None" = None) -> None:
        self.value = value
        self.next = next_node


class Queue:
    """FIFO Queue backed by a singly linked list with front and rear pointers.

    Why linked-list-based instead of a Python list:
    - Removing from the front of a Python list (`pop(0)`) shifts every element and
      takes O(n). With `head` and `tail` pointers, both `enqueue` and `dequeue`
      run in strict O(1) time.
    - Supports `remove_value` because a user may accept, reject, or cancel a
      connection request out of arrival order.
    """

    def __init__(self) -> None:
        """Create an empty queue.

        Time: O(1)
        Space: O(1)
        """
        self._head: _QueueNode | None = None
        self._tail: _QueueNode | None = None
        self._size: int = 0

    def enqueue(self, value: Any) -> None:
        """Append `value` to the rear of the queue.

        Time: O(1)
        Space: O(1)
        """
        new_node = _QueueNode(value)
        if self._tail is None:
            # Queue was empty, so both head and tail point to the single node.
            self._head = new_node
            self._tail = new_node
        else:
            self._tail.next = new_node
            self._tail = new_node
        self._size += 1

    def dequeue(self) -> Any:
        """Remove and return the front item of the queue.

        Raises IndexError if the queue is empty.

        Time: O(1)
        Space: O(1)
        """
        if self._head is None:
            raise IndexError("Cannot dequeue from an empty queue.")
        value = self._head.value
        self._head = self._head.next
        if self._head is None:
            # Queue became empty, so clear the rear pointer too.
            self._tail = None
        self._size -= 1
        return value

    def peek(self) -> Any:
        """Return the front item without removing it.

        Raises IndexError if the queue is empty.

        Time: O(1)
        Space: O(1)
        """
        if self._head is None:
            raise IndexError("Cannot peek at an empty queue.")
        return self._head.value

    def is_empty(self) -> bool:
        """Return True if the queue has no items.

        Time: O(1)
        Space: O(1)
        """
        return self._head is None

    def remove_value(self, target: Any) -> bool:
        """Remove the first occurrence equal to `target` from anywhere in the queue.

        Needed when a connection request is accepted, rejected, or cancelled
        out of FIFO order. Returns True if removed, False otherwise.

        Time: O(n)
        Space: O(1)
        """
        previous: _QueueNode | None = None
        current = self._head

        while current is not None:
            if current.value == target:
                if previous is None:
                    self._head = current.next
                else:
                    previous.next = current.next

                # If we deleted the last node, move tail back to previous.
                if current is self._tail:
                    self._tail = previous

                self._size -= 1
                return True

            previous = current
            current = current.next

        return False

    def remove_where(self, predicate: Callable[[Any], bool]) -> Any | None:
        """Remove and return the first item satisfying `predicate`, or None.

        Time: O(n)
        Space: O(1)
        """
        previous: _QueueNode | None = None
        current = self._head

        while current is not None:
            if predicate(current.value):
                if previous is None:
                    self._head = current.next
                else:
                    previous.next = current.next

                if current is self._tail:
                    self._tail = previous

                self._size -= 1
                return current.value

            previous = current
            current = current.next

        return None

    def to_list(self) -> list[Any]:
        """Return all queued items from front to rear as a list.

        Time: O(n)
        Space: O(n)
        """
        result: list[Any] = []
        current = self._head
        while current is not None:
            result.append(current.value)
            current = current.next
        return result

    def __len__(self) -> int:
        """Return the number of items currently in the queue.

        Time: O(1)
        Space: O(1)
        """
        return self._size

    def __iter__(self) -> Iterator[Any]:
        """Iterate over items from front to rear without modifying the queue.

        Time: O(n)
        Space: O(1)
        """
        current = self._head
        while current is not None:
            yield current.value
            current = current.next
