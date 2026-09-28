type Flag is Data:
  Off{}
  On{}
type Value is Data:
  Value{value: Flag}
type Tree is Type:
  Leaf{value: Value}
  Fork{left: Tree, right: Tree}
def discard(tree: Tree) -> Flag:
  On{}
def main() -> Flag:
  discard(Fork{Leaf{Value{Off{}}},Leaf{Value{On{}}}})
