type Flag is Data:
  Off{}
  On{}

type Tree is Data:
  Stop{}
  Leaf{value: Flag}
  Branch{left: Tree, right: Tree}
