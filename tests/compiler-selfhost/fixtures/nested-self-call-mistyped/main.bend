# Twin of nested-self-call: the inner self-call passes a Tree where its suffix is Bits.
type Bit is Data:
  O{}
  I{}

type Bits is Data:
  End{}
  Push{head: Bit, tail: Bits}

type Tree is Data:
  Leaf{}
  Chunk{bit: Bit}
  Join{left: Tree, right: Tree}

def emit(tree: Tree, suffix: Bits) -> Bits:
  match tree:
    case Leaf{}: suffix
    case Chunk{bit}: Push{bit,suffix}
    case Join{left,right}: emit(left,emit(right,Leaf{}))

def main() -> Bits:
  emit(Join{Chunk{I{}},Chunk{O{}}},End{})
