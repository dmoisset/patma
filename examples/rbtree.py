from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from typing import Optional, TypeVar, Generic, Protocol, Iterator


class NodeColor(Enum):
    RED = auto()
    BLACK = auto()


class Direction(Enum):
    LEFT = auto()
    RIGHT = auto()


class Comparable(Protocol):
    def __lt__(self, other: Comparable): ...


T = TypeVar("T", bound=Comparable)


@dataclass(eq=False)
class RBNode(Generic[T]):
    value: T
    color: NodeColor
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


class NodeWalker(Generic[T]):
    def __init__(self, t: RBTree[T]) -> None:
        self.path = [t.root]
        self.tree = t
        self.leaf_direction = Direction.LEFT

    # Information
    def current(self) -> Optional[RBNode[T]]:
        return self.path[-1]

    def is_root(self):
        return len(self.path) == 1

    def parent(self):
        if len(self.path) <= 1:
            raise ValueError("No parent for rott")
        return self.path[-2]

    def is_left_child(self) -> bool:
        match self.path:
            case [root]: raise ValueError("this is not defined for the root")
            case [*_, None]: return self.leaf_direction == Direction.LEFT
            case [*_, parent, child]: return parent.left is child

    def is_right_child(self) -> bool:
        match self.path:
            case [root]: raise ValueError("this is not defined for the root")
            case [*_, None]: return self.leaf_direction == Direction.RIGHT
            case [*_, parent, child]: return parent.right is child

    # Tree walking
    def up(self) -> NodeWalker[T]:
        if self.is_root():
            raise ValueError("Can not go up from the root")
        self.path.pop()
        return self

    def left(self) -> NodeWalker[T]:
        c = self.current()
        if not c:
            raise ValueError("Can not go left from leaf")
        self.path.append(c.left)
        if not c.left:
            self.leaf_direction = Direction.LEFT
        return self

    def right(self) -> NodeWalker[T]:
        c = self.current()
        if not c:
            raise ValueError("Can not go right from leaf")
        self.path.append(c.right)
        if not c.right:
            self.leaf_direction = Direction.RIGHT
        return self

    # Tree modification
    def update(self, new_child: Optional[RBNode[T]]) -> None:
        if len(self.path) >= 2:
            new_parent = self.path[-2]
            assert new_parent
            if self.is_left_child():
                new_parent.left = new_child
            else:
                new_parent.right = new_child
            self.path[-1] = new_child
        else:  # we are at the root
            self.tree.root = new_child
            self.path = [new_child]


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
        w = NodeWalker(self)
        while node := w.current():
            if z.value < node.value:
                w.left()
            else:
                w.right()
        w.update(z)
        self._insert_fix(w)

    def _insert_fix(self, z: NodeWalker[T]) -> None:
        while not z.is_root() and z.parent().color == NodeColor.RED:
            c = z.current()
            z.up().up()
            match z.current():
                case RBNode(left=(parent := RBNode(left=l, right=r)), right=(uncle := RBNode(color=NodeColor.RED))) if c in (l, r):
                    # Case 1: right uncle is red
                    parent.color = NodeColor.BLACK
                    uncle.color = NodeColor.BLACK
                    z.current().color = NodeColor.RED
                case RBNode(left=RBNode(right=r), right=RBNode(color=NodeColor.BLACK)|None) if c is r:
                    # Case 2: right uncle is black, z was right child
                    z.left()
                    self._left_rotate(z)
                case RBNode(left=(parent := RBNode(left=l)), right=RBNode(color=NodeColor.BLACK)|None) if c is l:
                    # Case 3: right uncle is black, z was left child
                    parent.color = NodeColor.BLACK
                    z.current().color = NodeColor.RED
                    self._right_rotate(z)
                case RBNode(right=(parent := RBNode(left=l, right=r)), left=(uncle := RBNode(color=NodeColor.RED))) if c in (l, r):
                    # Case 1': left uncle is red
                    parent.color = NodeColor.BLACK
                    uncle.color = NodeColor.BLACK
                    z.current().color = NodeColor.RED
                case RBNode(left=RBNode(color=NodeColor.BLACK)|None, right=RBNode(left=l)) if c is l:
                    # Case 2': left uncle is black, z was left child
                    z.right()
                    self._right_rotate(z)
                case RBNode(left=RBNode(color=NodeColor.BLACK)|None, right=(parent := RBNode(right=r))) if c is r:
                    # Case 3': left uncle is black, z was right child
                    parent.color = NodeColor.BLACK
                    z.current().color = NodeColor.RED
                    self._left_rotate(z)
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
        # All paths from any node have the same number of black nodes
        return bpbalance(self.root) is not None

    def _left_rotate(self, w: NodeWalker[T]) -> None:
        x = w.current()
        assert x.right
        y = x.right
        w.update(RBNode(y.value, y.color, RBNode(x.value, x.color, x.left, y.left), y.right))
        w.left()  # Follow x

    def _right_rotate(self, w: NodeWalker[T]) -> None:
        y = w.current()
        assert y.left
        x = y.left
        w.update(RBNode(x.value, x.color, x.left, RBNode(y.value, y.color, x.right, y.right)))
        w.right()  # Follow y


if __name__ == "__main__":
    import random
    N = 255
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
