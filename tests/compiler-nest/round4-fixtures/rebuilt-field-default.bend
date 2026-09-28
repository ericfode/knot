type Flag is Data:
  Off{}
  On{}

type T is Data:
  Leaf{}
  Node{l: T, v: Flag}

def len(t: T) -> Flag:
  match t:
    case Leaf{}: On{}
    case Node{Node{_, On{}}, Off{}}: Off{}
    case Node{l, v}: len(l)

def e(+a: Flag, b: Flag) -> Flag:
  len(Node{Node{Node{Leaf{}, a}, b}, a})

def main() -> Flag:
  e(On{}, Off{})
