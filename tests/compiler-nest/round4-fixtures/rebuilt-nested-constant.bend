type Flag is Data:
  Off{}
  On{}

type T is Data:
  Leaf{}
  Node{l: T, v: Flag}

def len(t: T) -> Flag:
  match t:
    case Leaf{}: On{}
    case Node{Node{Node{a, On{}}, b}, c}: len(Node{a, On{}})
    case Node{l, v}: Off{}

def main() -> Flag:
  len(Node{Node{Node{Leaf{}, On{}}, Off{}}, Off{}})
