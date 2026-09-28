# Closed ~ arguments built from generic defs: ident(Flag) partially applied, and a lambda calling pick at Flag.
type Flag is Data:
  Off{}
  On{}

type Seq<a, -A: Kind(a)> is Kind(a):
  Stop{}
  Link{head: A, tail: Seq<a, A>}

def map(~A: Type, ~B: Type, ~f: A -> B, xs: Seq<A>) -> Seq<B>:
  match xs:
    case Stop{}: Stop{}
    case Link{h,t}: Link{f(h),map(~A,~B,~f,t)}

def ident(-A: Type, x: A) -> A:
  x

def pick(-A: Type, c: Flag, x: A, y: A) -> A:
  match c:
    case On{}: x
    case Off{}: y

def first(xs: Seq<Flag>) -> Flag:
  match xs:
    case Stop{}: Off{}
    case Link{h,t}: h

def same(a: Flag) -> Flag:
  first(map(~Flag,~Flag,~ident(Flag),Link{a,Stop{}}))

def flipped(a: Flag) -> Flag:
  first(map(~Flag,~Flag,~(x => pick(Flag,x,Off{},On{})),Link{a,Stop{}}))

def main() -> Flag:
  flipped(On{})
