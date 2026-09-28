# A self-call in another self-call's argument: emit(left,emit(right,suffix)),
# the shape of ByteOutput's emit (bytes.bend:80-81), over local types.
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

type Cell is Type:
  Low{}
  High{}
  Gap{}

type Pos is Type:
  P0{}
  P1{}
  P2{}
  P3{}
  P4{}

def emit(tree: Tree, suffix: Bits) -> Bits:
  match tree:
    case Leaf{}: suffix
    case Chunk{bit}: Push{bit,suffix}
    case Join{left,right}: emit(left,emit(right,suffix))

def cell(b: Bit) -> Cell:
  match b:
    case O{}: Low{}
    case I{}: High{}

def nth(bits: Bits, p: Pos) -> Cell:
  match bits:
    case End{}: Gap{}
    case Push{head,tail}:
      match p:
        case P0{}: cell(head)
        case P1{}: nth(tail,P0{})
        case P2{}: nth(tail,P1{})
        case P3{}: nth(tail,P2{})
        case P4{}: nth(tail,P3{})

# Emits I,O,O before the suffix; any other nesting order changes some position.
def sample() -> Tree:
  Join{Join{Chunk{I{}},Leaf{}},Join{Chunk{O{}},Chunk{O{}}}}

def at(p: Pos) -> Cell:
  nth(emit(sample(),Push{I{},End{}}),p)

def main() -> Cell:
  at(P3{})
