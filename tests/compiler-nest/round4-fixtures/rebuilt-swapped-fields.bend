type Flag is Data:
  Off{}
  On{}

type Tree is Data:
  Leaf{}
  Node{l: Tree, r: Tree}

def f(t: Tree) -> Flag:
  match t:
    case Leaf{}: On{}
    case Node{Node{a, b}, r}: f(Node{b, a})
    case Node{l, r}: Off{}

def main() -> Flag:
  f(Node{Node{Leaf{}, Leaf{}}, Leaf{}})
