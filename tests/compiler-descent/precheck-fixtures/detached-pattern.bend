type Flag is Data:
  Off{}
  On{}

type T is Type:
  Leaf{v: Flag}
  Node{l: T, r: T}

def lm(t: T) -> Flag:
  match t:
    case Node {Leaf{On{}}, r}: lm(r)
    case Node{l, r}: lm(l)
    case Leaf{v}: v

def p(+a: Flag, b: Flag) -> Flag:
  lm(Node{Node{Leaf{a}, Leaf{b}}, Leaf{a}})

def main() -> Flag:
  On{}
