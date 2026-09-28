type Flag is Data:
  Off{}
  On{}
type Tree is Type:
  Leaf{value: Flag}
  Fork{left: Tree, right: Tree}
def mirror(tree: Tree) -> Tree:
  match tree:
    case Leaf{value}: Leaf{value}
    case Fork{left,right}: Fork{mirror(right),mirror(left)}
def main() -> Tree:
  mirror(Fork{Leaf{Off{}},Fork{Leaf{On{}},Leaf{Off{}}}})
