type Flag is Data:
  Off{}
  On{}
type Tree is Data:
  Leaf{value: Flag}
  Fork{left: Tree, right: Tree}
def main() -> Flag:
  On{}
