type Flag is Data:
  Off{}
  On{}

type T is Data:
  Leaf{}
  Node{l: T, v: Flag}

def len(t: T) -> Flag:
  match t:
    case Leaf{}: On{}
    case Node{l, v}: len(Leaf{})

def main() -> Flag:
  len(Node{Leaf{}, Off{}})
