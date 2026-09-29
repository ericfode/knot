type Flag is Data:
  Off{}
  On{}

type T is Data:
  Leaf{}
  Node{l: T, v: Flag}

def len(t: T) -> Flag:
  match t:
    case Leaf{}: On{}
    case Node{l, v}:
      match l:
        case Leaf{}: len(l)
        case Node{a, b}: len(l)

def main() -> Flag:
  len(Node{Node{Leaf{}, On{}}, Off{}})
