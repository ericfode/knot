# The Base List.any shape, and a template forwarding its ~a, ~A and ~f to foldl inside a closed ~ lambda.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Seq<a, -A: Kind(a)> is Kind(a):
  Stop{}
  Link{head: A, tail: Seq<a, A>}

def or(x: Flag, y: Flag) -> Flag:
  match x:
    case Off{}: y
    case On{}: On{}

def and(x: Flag, y: Flag) -> Flag:
  match x:
    case Off{}: Off{}
    case On{}: y

def any(~a: Quant, ~A: Kind(a), ~f: A -> Flag, xs: Seq<a, A>) -> Flag:
  match xs:
    case Stop{}: Off{}
    case Link{h,t}: or(f(h),any(~a,~A,~f,t))

def foldl(~a: Quant, ~A: Kind(a), ~B: Type, ~f: B -> A -> B, xs: Seq<a, A>, acc: B) -> B:
  match xs:
    case Stop{}: acc
    case Link{h,t}: foldl(~a,~A,~B,~f,t,f(acc,h))

def all(~a: Quant, ~A: Kind(a), ~f: A -> Flag, xs: Seq<a, A>) -> Flag:
  foldl(~a,~A,~Flag,~(acc => h => and(acc,f(h))),xs,On{})

def blue(c: Color) -> Flag:
  match c:
    case Red{}: Off{}
    case Blue{}: On{}

def some_blue(a: Color, b: Color) -> Flag:
  any(~&2,~Color,~blue,Link{a,Link{b,Stop{}}})

def all_blue(a: Color, b: Color) -> Flag:
  all(~&2,~Color,~blue,Link{a,Link{b,Stop{}}})

def any_arrow(x: Flag, g: Flag) -> Flag:
  any(~&1,~(Flag -> Flag),~(k => k(On{})),Link{y => and(x,y),Link{y => and(g,y),Stop{}}})

def main() -> Flag:
  all_blue(Blue{},Red{})
