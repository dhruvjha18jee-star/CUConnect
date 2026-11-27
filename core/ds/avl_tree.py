# core/ds/avl_tree.py
# Hand-written Self-Balancing AVL Tree with LL, RR, LR, and RL rotations.
# Course mapping: Session 10: AVL Trees & Session 9: Binary Trees (BST).

from typing import Any


class AVLNode:
    """Node inside an AVL tree storing key, value, child links, and subtree height."""

    def __init__(self, key: Any, value: Any) -> None:
        """Create a leaf AVLNode storing `(key, value)` with initial height 1.

        Time: O(1)
        Space: O(1)
        """
        self.key = key
        self.value = value
        self.left: "AVLNode | None" = None
        self.right: "AVLNode | None" = None
        self.height: int = 1


class AVLTree:
    """Self-balancing Binary Search Tree maintaining |balance_factor| <= 1.

    Used in CUConnect to maintain the alphabetical "Browse All Students" directory
    without re-sorting on every page view:
    - Insert, delete, and search all stay O(log n) even if students sign up in
      strictly alphabetical order (which would degenerate a plain BST to O(n)).
    - In-order traversal yields all students in exact alphabetical order in O(n).
    """

    def __init__(self) -> None:
        """Create an empty AVL tree.

        Time: O(1)
        Space: O(1)
        """
        self._root: AVLNode | None = None
        self._size: int = 0

    def _node_height(self, node: AVLNode | None) -> int:
        """Return height of a node (0 for None)."""
        return node.height if node is not None else 0

    def _update_height(self, node: AVLNode) -> None:
        """Recompute a node's height from its two children."""
        left_h = self._node_height(node.left)
        right_h = self._node_height(node.right)
        node.height = 1 + (left_h if left_h >= right_h else right_h)

    def _balance_factor(self, node: AVLNode | None) -> int:
        """Return height(left) - height(right); valid AVL range is [-1, +1]."""
        if node is None:
            return 0
        return self._node_height(node.left) - self._node_height(node.right)

    def _rotate_right(self, y: AVLNode) -> AVLNode:
        """Perform a single Right Rotation to fix an LL (left-heavy) imbalance.

              y                x
             / \\              / \\
            x   T3   --->   T1   y
           / \\                  / \\
          T1  T2               T2  T3
        """
        x = y.left
        assert x is not None
        t2 = x.right

        x.right = y
        y.left = t2

        # Update child `y` first because `x`'s new height depends on `y`.
        self._update_height(y)
        self._update_height(x)
        return x

    def _rotate_left(self, x: AVLNode) -> AVLNode:
        """Perform a single Left Rotation to fix an RR (right-heavy) imbalance.

            x                  y
           / \\                / \\
          T1  y     --->     x   T3
             / \\            / \\
            T2  T3         T1  T2
        """
        y = x.right
        assert y is not None
        t2 = y.left

        y.left = x
        x.right = t2

        # Update child `x` first because `y`'s new height depends on `x`.
        self._update_height(x)
        self._update_height(y)
        return y

    def _rebalance(self, node: AVLNode) -> AVLNode:
        """Check balance factor and apply LL, LR, RR, or RL rotations if needed."""
        self._update_height(node)
        balance = self._balance_factor(node)

        # Left-heavy cases: LL or LR.
        if balance > 1:
            assert node.left is not None
            if self._balance_factor(node.left) < 0:
                # LR case: left child is right-heavy -> left-rotate child, then right-rotate node.
                node.left = self._rotate_left(node.left)
            # LL case (or second step of LR): right-rotate node.
            return self._rotate_right(node)

        # Right-heavy cases: RR or RL.
        if balance < -1:
            assert node.right is not None
            if self._balance_factor(node.right) > 0:
                # RL case: right child is left-heavy -> right-rotate child, then left-rotate node.
                node.right = self._rotate_right(node.right)
            # RR case (or second step of RL): left-rotate node.
            return self._rotate_left(node)

        return node

    def _insert_node(self, node: AVLNode | None, key: Any, value: Any) -> tuple[AVLNode, bool]:
        """Recursive BST insert followed by bottom-up AVL rebalancing."""
        if node is None:
            return AVLNode(key, value), True

        if key < node.key:
            node.left, inserted = self._insert_node(node.left, key, value)
        elif key > node.key:
            node.right, inserted = self._insert_node(node.right, key, value)
        else:
            # Update existing key in place without changing tree shape.
            node.value = value
            return node, False

        return self._rebalance(node), inserted

    def _min_node(self, node: AVLNode) -> AVLNode:
        """Return the leftmost (minimum-key) node in the given non-empty subtree."""
        current = node
        while current.left is not None:
            current = current.left
        return current

    def _delete_node(self, node: AVLNode | None, key: Any) -> tuple[AVLNode | None, bool]:
        """Recursive BST delete followed by bottom-up AVL rebalancing."""
        if node is None:
            return None, False

        if key < node.key:
            node.left, deleted = self._delete_node(node.left, key)
        elif key > node.key:
            node.right, deleted = self._delete_node(node.right, key)
        else:
            deleted = True
            # Case 1 & 2: zero or one child.
            if node.left is None:
                return node.right, True
            if node.right is None:
                return node.left, True

            # Case 3: two children -> replace with in-order successor from right subtree.
            successor = self._min_node(node.right)
            node.key = successor.key
            node.value = successor.value
            node.right, _ = self._delete_node(node.right, successor.key)

        if not deleted:
            return node, False

        return self._rebalance(node), True

    def insert(self, key: Any, value: Any) -> None:
        """Insert `(key, value)` into the AVL tree, or update `value` if `key` exists.

        Time: O(log n)
        Space: O(log n) recursion stack
        """
        self._root, inserted = self._insert_node(self._root, key, value)
        if inserted:
            self._size += 1

    def delete(self, key: Any) -> bool:
        """Delete `key` from the AVL tree and rebalance. Returns True if removed.

        Time: O(log n)
        Space: O(log n) recursion stack
        """
        self._root, deleted = self._delete_node(self._root, key)
        if deleted:
            self._size -= 1
        return deleted

    def search(self, key: Any) -> Any | None:
        """Return the value mapped to `key`, or None if not found.

        Time: O(log n)
        Space: O(1)
        """
        current = self._root
        while current is not None:
            if key == current.key:
                return current.value
            if key < current.key:
                current = current.left
            else:
                current = current.right
        return None

    def inorder(self) -> list[Any]:
        """Return all stored values in ascending key order via in-order traversal.

        Time: O(n)
        Space: O(n)
        """
        result: list[Any] = []

        def _walk(node: AVLNode | None) -> None:
            if node is None:
                return
            _walk(node.left)
            result.append(node.value)
            _walk(node.right)

        _walk(self._root)
        return result

    def height(self) -> int:
        """Return the current height of the AVL tree (0 if empty).

        Time: O(1)
        Space: O(1)
        """
        return self._node_height(self._root)

    def is_balanced(self) -> bool:
        """Verify that every node satisfies |balance_factor| <= 1 and BST order.

        Time: O(n)
        Space: O(log n)
        """
        def _check(node: AVLNode | None) -> bool:
            if node is None:
                return True
            bf = self._balance_factor(node)
            if bf < -1 or bf > 1:
                return False
            if node.left is not None and node.left.key >= node.key:
                return False
            if node.right is not None and node.right.key <= node.key:
                return False
            return _check(node.left) and _check(node.right)

        return _check(self._root)

    def __len__(self) -> int:
        """Return the number of entries stored in the AVL tree.

        Time: O(1)
        Space: O(1)
        """
        return self._size
