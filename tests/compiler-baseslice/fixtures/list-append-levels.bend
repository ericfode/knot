import Base

type Levels is Data:
  Nought{}
  Seven{}
  ThreeFive{}

type Front is Data:
  NoFront{}
  FrontThree{}
  FrontSeven{}
  FrontOther{}

type Size is Data:
  Size0{}
  Size1{}
  Size2{}
  Size3{}
  Size4{}
  SizeOther{}

def levels(l: Levels) -> List<&2, U32>:
  match l:
    case Nought{}: []
    case Seven{}: [7]
    case ThreeFive{}: [3, 5]

# scope.bend: List.append(&2, U32, fields, smaller).
def joined(l: Levels, r: Levels) -> List<&2, U32>:
  List.append(&2, U32, levels(l), levels(r))

def front_of(xs: List<&2, U32>) -> Front:
  match xs:
    case Nil{}: NoFront{}
    case Con{+h, t}:
      Bool.pick(Front, U32.is_eq(h, 3), FrontThree{},
        Bool.pick(Front, U32.is_eq(h, 7), FrontSeven{}, FrontOther{}))

def size_of(+n: U32) -> Size:
  Bool.pick(Size, U32.is_eq(n, 0), Size0{},
  Bool.pick(Size, U32.is_eq(n, 1), Size1{},
  Bool.pick(Size, U32.is_eq(n, 2), Size2{},
  Bool.pick(Size, U32.is_eq(n, 3), Size3{},
  Bool.pick(Size, U32.is_eq(n, 4), Size4{}, SizeOther{})))))

def front(l: Levels, r: Levels) -> Front:
  front_of(joined(l, r))

def size(l: Levels, r: Levels) -> Size:
  size_of(U32.from_nat(List.length(&2, U32, joined(l, r))))

def main() -> Front:
  front(Seven{}, ThreeFive{})
