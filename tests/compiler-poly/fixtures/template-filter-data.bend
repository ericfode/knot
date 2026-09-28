# The Base List.filter shape: ~A: Data over Seq<&2,A>, a + head binder, and ~A passed on as an erased type argument.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Seq<a, -A: Kind(a)> is Kind(a):
  Stop{}
  Link{head: A, tail: Seq<a, A>}

def put(-A: Data, h: A, r: Seq<&2,A>, keep: Flag) -> Seq<&2,A>:
  match keep:
    case Off{}: r
    case On{}: Link{h,r}

def filter(~A: Data, ~f: A -> Flag, xs: Seq<&2,A>) -> Seq<&2,A>:
  match xs:
    case Stop{}: Stop{}
    case Link{+h,t}: put(A,h,filter(~A,~f,t),f(h))

def blue(c: Color) -> Flag:
  match c:
    case Red{}: Off{}
    case Blue{}: On{}

def head_or(xs: Seq<&2,Color>, d: Color) -> Color:
  match xs:
    case Stop{}: d
    case Link{h,t}: h

def count_two(xs: Seq<&2,Flag>) -> Flag:
  match xs:
    case Stop{}: Off{}
    case Link{h,t}:
      match t:
        case Stop{}: Off{}
        case Link{h2,t2}: On{}

def blues(a: Color, b: Color) -> Color:
  head_or(filter(~Color,~blue,Link{a,Link{b,Stop{}}}),Red{})

def ons(a: Flag, b: Flag) -> Flag:
  count_two(filter(~Flag,~(x => x),Link{a,Link{b,Stop{}}}))

def main() -> Color:
  blues(Red{},Blue{})
