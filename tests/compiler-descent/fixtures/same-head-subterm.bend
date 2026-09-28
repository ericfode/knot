type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
type Tree is Data:
  Leaf{}
  Fork{left: Tree, right: Tree}
def drain(tree: Tree) -> Flag:
  match tree:
    case Leaf{}: On{}
    case Fork{Leaf{},_}: Off{}
    case Fork{Fork{x,y},_}: drain(Fork{x,y})
def main() -> Flag:
  drain(Fork{Fork{Fork{Leaf{},Leaf{}},Leaf{}},Leaf{}})
