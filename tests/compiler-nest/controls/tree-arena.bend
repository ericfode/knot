# Complete binary trees exhaust the fixed arena before returning a partial value.
type Flag is Data:
  Off{}
  On{}
type Depth is Data:
  Zero{}
  More{pred: Depth}
type Tree is Data:
  Leaf{value: Flag}
  Fork{left: Tree, right: Tree}

def grow(+n: Depth) -> Tree:
  match n:
    case Zero{}: Leaf{On{}}
    case More{p}: Fork{grow(p), grow(p)}

def left(t: Tree) -> Flag:
  match t:
    case Leaf{v}: v
    case Fork{Leaf{v}, _}: v
    case Fork{Fork{a, b}, _}: left(a)

def shallow() -> Flag:
  left(grow(More{More{More{More{Zero{}}}}}))

def main() -> Flag:
  left(grow(More{More{More{More{More{More{More{More{More{More{More{More{Zero{}}}}}}}}}}}}}))
