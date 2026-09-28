import Base

type Value is Data:
  Nought{}
  SixtyThree{}
  SixtyFour{}
  Seven7F{}
  Eighty{}
  Sample{}
  SignedMax{}
  Largest{}

type Sign is Data:
  Unsigned{}
  Signed{}

type Width is Data:
  Width1{}
  Width2{}
  Width3{}
  Width4{}
  Width5{}
  WidthOther{}

type Verdict is Data:
  Wrong{}
  Exact{}

def value(v: Value) -> U32:
  match v:
    case Nought{}: 0
    case SixtyThree{}: 63
    case SixtyFour{}: 64
    case Seven7F{}: 127
    case Eighty{}: 128
    case Sample{}: 624485
    case SignedMax{}: 2147483647
    case Largest{}: 4294967295

def signed(s: Sign) -> Bool:
  match s:
    case Unsigned{}: False{}
    case Signed{}: True{}

# wasm-bytes.groups: seven-bit groups, low first, with a continuation bit;
# a signed final group keeps its sixth bit clear. Five groups cover U32.
def groups(fuel: Nat, +signed: Bool, +value: U32) -> List<&2, U32>:
  match fuel:
    case 0n: Nil{}
    case 1n+n:
      Bool.pick(List<&2, U32>, U32.is_lt(value, Bool.pick(U32, signed, 64, 128)), [value],
        Con{U32.add(U32.and(value, 127), 128), groups(n, signed, U32.shrn(value, 7n))})

def expected(v: Value, s: Sign) -> List<&2, U32>:
  match v s:
    case Nought{} _: [0]
    case SixtyThree{} _: [63]
    case SixtyFour{} Unsigned{}: [64]
    case SixtyFour{} Signed{}: [192, 0]
    case Seven7F{} Unsigned{}: [127]
    case Seven7F{} Signed{}: [255, 0]
    case Eighty{} _: [128, 1]
    case Sample{} _: [229, 142, 38]
    case SignedMax{} _: [255, 255, 255, 255, 7]
    case Largest{} _: [255, 255, 255, 255, 15]

def same(xs: List<&2, U32>, ys: List<&2, U32>) -> Bool:
  match xs ys:
    case Nil{} Nil{}: True{}
    case Con{x, xt} Con{y, yt}: Bool.and(U32.is_eq(x, y), same(xt, yt))
    case _ _: False{}

def width_of(+n: U32) -> Width:
  Bool.pick(Width, U32.is_eq(n, 1), Width1{},
  Bool.pick(Width, U32.is_eq(n, 2), Width2{},
  Bool.pick(Width, U32.is_eq(n, 3), Width3{},
  Bool.pick(Width, U32.is_eq(n, 4), Width4{},
  Bool.pick(Width, U32.is_eq(n, 5), Width5{}, WidthOther{})))))

def width(v: Value, s: Sign) -> Width:
  width_of(U32.from_nat(List.length(&2, U32, groups(5n, signed(s), value(v)))))

def exact(+v: Value, +s: Sign) -> Verdict:
  Bool.pick(Verdict, same(groups(5n, signed(s), value(v)), expected(v, s)), Exact{}, Wrong{})

def main() -> Width:
  width(Sample{}, Unsigned{})
