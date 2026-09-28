# U32.or, U32.xor, U32.not and U32.shln on the edge words 0, 1, 2^31 and
# 2^32-1 (base-pin's SHA-256 and machine-code's LEB128 reach them).
import Base

type Edge is Data:
  W0{}
  W1{}
  WHigh{}
  WMax{}

type Op is Type:
  Or{}
  Xor{}
  Not{}
  Shl1{}
  Shl31{}

type Class is Type:
  C0{}
  C1{}
  C2{}
  CHigh{}
  CHighOne{}
  CLow31{}
  CMaxLess{}
  CMax{}
  COther{}

def value(w: Edge) -> U32:
  match w:
    case W0{}: 0
    case W1{}: 1
    case WHigh{}: 2147483648
    case WMax{}: 4294967295

def apply(o: Op, a: U32, b: U32) -> U32:
  match o:
    case Or{}: U32.or(a,b)
    case Xor{}: U32.xor(a,b)
    case Not{}: U32.not(a)
    case Shl1{}: U32.shln(a,1n)
    case Shl31{}: U32.shln(a,31n)

def last(less: Bool, max: Bool) -> Class:
  match less:
    case True{}: CMaxLess{}
    case False{}:
      match max:
        case True{}: CMax{}
        case False{}: COther{}

def top(+x: U32, one: Bool, low: Bool) -> Class:
  match one:
    case True{}: CHighOne{}
    case False{}:
      match low:
        case True{}: CLow31{}
        case False{}: last(U32.is_eq(x,4294967294),U32.is_eq(x,4294967295))

def upper(+x: U32, e2: Bool, high: Bool) -> Class:
  match e2:
    case True{}: C2{}
    case False{}:
      match high:
        case True{}: CHigh{}
        case False{}: top(x,U32.is_eq(x,2147483649),U32.is_eq(x,2147483647))

def ladder(+x: U32, e0: Bool, e1: Bool) -> Class:
  match e0:
    case True{}: C0{}
    case False{}:
      match e1:
        case True{}: C1{}
        case False{}: upper(x,U32.is_eq(x,2),U32.is_eq(x,2147483648))

def classify(+x: U32) -> Class:
  ladder(x,U32.is_eq(x,0),U32.is_eq(x,1))

def probe(o: Op, a: Edge, b: Edge) -> Class:
  classify(apply(o,value(a),value(b)))

def main() -> Class:
  probe(Xor{},WMax{},WHigh{})
