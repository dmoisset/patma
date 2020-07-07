from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from typing import Optional, TypeVar, Generic, Protocol, Iterator


class NodeColor(Enum):
    RED = auto()
    BLACK = auto()


class Comparable(Protocol):
    def __lt__(self, other: Comparable): ...


T = TypeVar("T", bound=Comparable)


@dataclass
class RBNode(Generic[T]):
    value: T
    color: NodeColor
    parent: Optional[RBNode] = None
    left: Optional[RBNode] = None
    right: Optional[RBNode] = None

    def __iter__(self) -> Iterator[T]:
        if self.left:
            yield from self.left
        yield self.value
        if self.right:
            yield from self.right

    def nodes(self) -> Iterator[RBNode[T]]:
        if self.left:
            yield from self.left.nodes()
        yield self
        if self.right:
            yield from self.right.nodes()

    def depth(self) -> int:
        result = 0
        if self.left:
            result = max(result, self.left.depth())
        if self.right:
            result = max(result, self.right.depth())
        return result + 1


@dataclass
class RBTree(Generic[T]):
    root: Optional[RBNode[T]] = None

    def __contains__(self, value: T) -> bool:
        node = self.root
        while node:
            if value == node.value:
                return True
            elif value < node.value:
                node = node.left
            else:  # value > node.data
                node = node.right
        return False

    def add(self, value: T) -> None:
        z = RBNode(value, NodeColor.RED)
        y = None
        x = self.root
        while x:
            y = x
            if z.value < x.value:
                x = x.left
            else:
                x = x.right
        z.parent = y
        if not y:
            self.root = z
        elif z.value < y.value:
            y.left = z
        else:
            y.right = z
        self._insert_fix(z)

    def _insert_fix(self, z: RBNode[T]) -> None:
        while z.parent and z.parent.color == NodeColor.RED:
            if z.parent is z.parent.parent.left:
                y = z.parent.parent.right
                if y and y.color == NodeColor.RED:
                    z.parent.color = NodeColor.BLACK
                    y.color = NodeColor.BLACK
                    z.parent.parent.color = NodeColor.RED
                    z = z.parent.parent
                else:
                    if z is z.parent.right:
                        z = z.parent
                        self._left_rotate(z)
                    z.parent.color = NodeColor.BLACK
                    z.parent.parent.color = NodeColor.RED
                    self._right_rotate(z.parent.parent)
            else:
                y = z.parent.parent.left
                if y and y.color == NodeColor.RED:
                    z.parent.color = NodeColor.BLACK
                    y.color = NodeColor.BLACK
                    z.parent.parent.color = NodeColor.RED
                    z = z.parent.parent
                else:
                    if z is z.parent.left:
                        z = z.parent
                        self._right_rotate(z)
                    z.parent.color = NodeColor.BLACK
                    z.parent.parent.color = NodeColor.RED
                    self._left_rotate(z.parent.parent)
        self.root.color = NodeColor.BLACK            


    def __iter__(self) -> Iterator[T]:
        if self.root:
            return iter(self.root)
        else:
            return iter(())

    def invariant(self) -> bool:
        """
        True if the tree satisfies the red-black invariant:
        
        - root is black
        - if a node is red, both its childrens are black (None counts as black)
        - for each node, all paths from a node to descendant leafs have the same number of black nodes
        """
        def bpbalance(node: Optional[RBNode[T]]) -> Optional[int]:
            if not node:
                return 1
            l = bpbalance(node.left)
            if l is None:
                return None  # left tree is not black-path-balanced
            r = bpbalance(node.right)
            if r is None:
                return None  # right tree is not black-path-balanced
            if l != r:
                return None
            return l + int(node.color == NodeColor.BLACK)

        if not self.root:
            return True
        if self.root.color == NodeColor.RED:
            return False
        for n in self.root.nodes():
            # red nodes do not have red children
            if n.color == NodeColor.RED:
                if any(ch.color == NodeColor.RED for ch in (n.left, n.right) if ch):
                    return False
            # Check consistency of parents
            if n.left and n.left.parent is not n:
                return False
            if n.right and n.right.parent is not n:
                return False
        # All paths from any node have the same number of black nodes
        return bpbalance(self.root) is not None

    def _left_rotate(self, x: RBNode) -> None:
        assert x.right
        y = x.right
        x.right = y.left
        if y.left:
            y.left.parent = x
        y.parent = x.parent
        if not x.parent:
            self.root = y
        elif x is x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y

    def _right_rotate(self, y: RBNode) -> None:
        assert y.left
        x = y.left
        y.left = x.right
        if x.right:
            x.right.parent = y
        x.parent = y.parent
        if not y.parent:
            self.root = x
        elif y is y.parent.right:
            y.parent.right = x
        else:
            y.parent.left = x
        x.right = y
        y.parent = x


if __name__ == "__main__":
    import random
    N = 256
    # Random insert
    t = RBTree()
    for i in range(N):
        t.add(random.randrange(1000))
    assert t.invariant()
    print(f"Depth = {t.root.depth()}, values=", list(t))
    # Linear insert
    t = RBTree()
    for i in range(N):
        t.add(i)
    assert t.invariant()
    print(f"Depth = {t.root.depth()}, values=", list(t))
