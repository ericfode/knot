import Base

type Name is Data:
  FlagName{}
  ColorName{}
  ParityName{}
  MissingName{}

type Slot is Data:
  Slot0{}
  Slot1{}
  Slot2{}
  SlotOther{}
  Absent{}

type Verdict is Data:
  Lost{}
  Found{}

def name(n: Name) -> String:
  match n:
    case FlagName{}: "Flag"
    case ColorName{}: "Color"
    case ParityName{}: "Parity"
    case MissingName{}: "Missing"

def names() -> List<&2, String>:
  ["Flag", "Color", "Parity"]

# catalog.find_type: count up with U32.add while names differ.
def find(xs: List<&2, String>, +wanted: String, +index: U32) -> Maybe<&2, U32>:
  match xs:
    case Nil{}: None{}
    case Con{h, t}:
      Bool.pick(Maybe<&2, U32>, String.eq(h, wanted), Some{index}, find(t, wanted, U32.add(index, 1)))

# catalog.type_at: count down with U32.sub until the index is zero.
def at(xs: List<&2, String>, +index: U32) -> Maybe<&2, String>:
  match xs:
    case Nil{}: None{}
    case Con{+h, t}:
      Bool.pick(Maybe<&2, String>, U32.is_eq(index, 0), Some{h}, at(t, U32.sub(index, 1)))

def slot_of(m: Maybe<&2, U32>) -> Slot:
  match m:
    case None{}: Absent{}
    case Some{+i}:
      Bool.pick(Slot, U32.is_eq(i, 0), Slot0{},
      Bool.pick(Slot, U32.is_eq(i, 1), Slot1{},
      Bool.pick(Slot, U32.is_eq(i, 2), Slot2{}, SlotOther{})))

def named(+wanted: String, m: Maybe<&2, String>) -> Verdict:
  match m:
    case None{}: Lost{}
    case Some{s}: Bool.pick(Verdict, String.eq(s, wanted), Found{}, Lost{})

def back(+wanted: String, m: Maybe<&2, U32>) -> Verdict:
  match m:
    case None{}: Lost{}
    case Some{i}: named(wanted, at(names(), i))

def slot(n: Name) -> Slot:
  slot_of(find(names(), name(n), 0))

def roundtrip(n: Name) -> Verdict:
  +s = name(n)
  back(s, find(names(), s, 0))

def main() -> Slot:
  slot(ParityName{})
