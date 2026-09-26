type Tree is Type:
  Tip{}
  Branch{children: Forest}
type Forest is Type:
  Empty{}
  More{head: Tree, tail: Forest}
type Flag is Data:
  Off{}
  On{}
def main() -> Flag:
  On{}
