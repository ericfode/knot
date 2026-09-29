type Flag is Data:
  Off{}
  On{}

type Tree is Data:
  Leaf{}
  Node{l: Tree, v: Flag, r: Tree}

def xor(a: Flag, b: Flag) -> Flag:
  match a b:
    case Off{} y: y
    case On{} Off{}: On{}
    case On{} On{}: Off{}

def spine(t: Tree) -> Flag:
  match t:
    case Leaf{}: Off{}
    case Node{Node{_, On{}, _}, _, Node{_, Off{}, _}}: On{}
    case Node{l, v, r}: xor(spine(l), spine(r))

def e(+a: Flag, +b: Flag) -> Flag:
  spine(Node{Node{Node{Leaf{}, a, Leaf{}}, b, Leaf{}}, a, Node{Leaf{}, b, Node{Leaf{}, a, Leaf{}}}})

def main() -> Flag:
  e(On{}, Off{})
