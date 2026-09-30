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
    case Node{l, v}: len(t)

def main() -> Flag:
  len(Leaf{})
