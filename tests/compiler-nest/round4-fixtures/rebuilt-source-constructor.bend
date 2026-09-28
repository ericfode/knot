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
        case Leaf{}: Off{}
        case Node{a, b}: len(Node{a, b})

def main() -> Flag:
  len(Node{Node{Leaf{}, On{}}, Off{}})
