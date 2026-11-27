# core/ds/linked_list.py
# Hand-written Singly Linked List for newest-first per-user post streams.
# Course mapping: Session 4: Singly Linked Lists.

from typing import Any, Callable, Iterator


class ListNode:
    """Node in a singly linked list holding one item and a pointer to the next node."""

    def __init__(self, value: Any, next_node: "ListNode | None" = None) -> None:
        """Create a singly linked list node holding `value` and `next_node`.

        Time: O(1)
        Space: O(1)
        """
        self.value = value
        self.next = next_node


class SinglyLinkedList:
    """Singly linked list supporting O(1) head insertion, deletion, and traversal.

    Why a singly linked list for a user's posts:
    - Creating a post always prepends at the head in O(1) without shifting elements.
    - Because newer posts are always inserted at the head, the list stays naturally
      sorted newest-first, which allows the home feed to perform an O(k log k)
      k-way merge directly from each friend's `head` pointer.
    """

    def __init__(self) -> None:
        """Create an empty singly linked list.

        Time: O(1)
        Space: O(1)
        """
        self._head: ListNode | None = None
        self._size: int = 0

    @property
    def head(self) -> ListNode | None:
        """Return the first ListNode (or None if empty) for pointer-based traversal.

        Time: O(1)
        Space: O(1)
        """
        return self._head

    def is_empty(self) -> bool:
        """Return True if the list contains no nodes.

        Time: O(1)
        Space: O(1)
        """
        return self._head is None

    def insert_head(self, value: Any) -> ListNode:
        """Insert a new value at the front of the list and return its node.

        Time: O(1)
        Space: O(1)
        """
        new_node = ListNode(value, self._head)
        self._head = new_node
        self._size += 1
        return new_node

    def delete_value(self, target: Any) -> bool:
        """Delete the first node whose value equals `target`.

        Returns True if a node was removed, or False if `target` was not found.

        Time: O(n)
        Space: O(1)
        """
        previous: ListNode | None = None
        current = self._head

        while current is not None:
            if current.value == target:
                if previous is None:
                    self._head = current.next
                else:
                    previous.next = current.next
                self._size -= 1
                return True
            previous = current
            current = current.next

        return False

    def delete_by_id(self, target_id: Any, id_getter: Callable[[Any], Any]) -> Any | None:
        """Delete the first node where `id_getter(node.value) == target_id`.

        Returns the removed value, or None if no matching node exists.

        Time: O(n)
        Space: O(1)
        """
        previous: ListNode | None = None
        current = self._head

        while current is not None:
            if id_getter(current.value) == target_id:
                if previous is None:
                    self._head = current.next
                else:
                    previous.next = current.next
                self._size -= 1
                return current.value
            previous = current
            current = current.next

        return None

    def traverse(self) -> list[Any]:
        """Traverse from head to tail and return all values in order.

        Time: O(n)
        Space: O(n)
        """
        items: list[Any] = []
        current = self._head
        while current is not None:
            items.append(current.value)
            current = current.next
        return items

    def __iter__(self) -> Iterator[Any]:
        """Yield values from head to tail without allocating an intermediate list.

        Time: O(n)
        Space: O(1)
        """
        current = self._head
        while current is not None:
            yield current.value
            current = current.next

    def __len__(self) -> int:
        """Return the number of nodes in the list.

        Time: O(1)
        Space: O(1)
        """
        return self._size
