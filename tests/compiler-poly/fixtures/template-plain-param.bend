# A ~ argument for a plain erased parameter: apply is not a template.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Seq<a, -A: Kind(a)> is Kind(a):
  Stop{}
  Link{head: A, tail: Seq<a, A>}

def map(~A: Type, ~B: Type, ~f: A -> B, xs: Seq<A>) -> Seq<B>:
  match xs:
    case Stop{}: Stop{}
    case Link{h,t}: Link{f(h),map(~A,~B,~f,t)}

def paint(f: Flag) -> Color:
  match f:
    case Off{}: Red{}
    case On{}: Blue{}

def tone(c: Color) -> Flag:
  match c:
    case Red{}: On{}
    case Blue{}: Off{}

def last_color(xs: Seq<Color>) -> Color:
  match xs:
    case Stop{}: Red{}
    case Link{h,t}:
      match t:
        case Stop{}: h
        case Link{h2,t2}: last_color(t)

def last_flag(xs: Seq<Flag>) -> Flag:
  match xs:
    case Stop{}: Off{}
    case Link{h,t}:
      match t:
        case Stop{}: h
        case Link{h2,t2}: last_flag(t)

def painted(a: Flag, b: Flag) -> Color:
  last_color(map(~Flag,~Color,~paint,Link{a,Link{b,Stop{}}}))

def toned(a: Color, b: Color) -> Flag:
  last_flag(map(~Color,~Flag,~(c => tone(c)),Link{a,Link{b,Stop{}}}))

def apply(-A: Type, -B: Type, f: A -> B, x: A) -> B:
  f(x)

def applied(a: Flag) -> Color:
  apply(~Flag,~Color,~paint,a)

def main() -> Color:
  painted(Off{},On{})
