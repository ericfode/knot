type Flag is Data:
  Off{}
  On{}

type T is Data:
  Leaf{}
  Node{l: T, v: Flag}

def len(t: T) -> Flag:
  match t:
    case Leaf{}: On{}
    case Node{l, Off{}}: len(Leaf{})
    case Node{l, On{}}: On{}

def main() -> Flag:
  len(Node{Node{Leaf{}, On{}}, Off{}})
