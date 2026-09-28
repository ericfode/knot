import Base

type Slots is Data:
  NoSlots{}
  OneSlot{}
  ThreeSlots{}

type Cell is Data:
  Bytes4{}
  Bytes8{}
  Bytes16{}
  BytesOther{}

type Budget is Data:
  Nought{}
  Three{}
  Offset{}
  PastOffset{}

type Order is Data:
  Below{}
  Level{}
  Above{}

def slots(s: Slots) -> List<&2, U32>:
  match s:
    case NoSlots{}: []
    case OneSlot{}: [0]
    case ThreeSlots{}: [0, 1, 2]

def budget(b: Budget) -> U32:
  match b:
    case Nought{}: 0
    case Three{}: 3
    case Offset{}: 256
    case PastOffset{}: 257

def cell_of(+bytes: U32) -> Cell:
  Bool.pick(Cell, U32.is_eq(bytes, 4), Bytes4{},
  Bool.pick(Cell, U32.is_eq(bytes, 8), Bytes8{},
  Bool.pick(Cell, U32.is_eq(bytes, 16), Bytes16{}, BytesOther{})))

def order(c: Cmp) -> Order:
  match c:
    case LT{}: Below{}
    case EQ{}: Level{}
    case GT{}: Above{}

# wasm.bend: a cell is a tag word plus one word per live field.
def cell(s: Slots) -> Cell:
  cell_of(U32.mul(4, U32.add(1, U32.from_nat(List.length(&2, U32, slots(s))))))

# driver.natural hands U32.to_nat to Nat fuel; 256n is the largest offset literal.
def fuel(b: Budget) -> Order:
  order(Nat.cmp(U32.to_nat(budget(b)), 256n))

def main() -> Cell:
  cell(ThreeSlots{})
