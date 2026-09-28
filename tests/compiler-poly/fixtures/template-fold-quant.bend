# The Base List.foldl shape: ~a: Quant and ~A: Kind(a) instantiated at &2 data and at &1 arrows folded by application.
type Flag is Data:
  Off{}
  On{}

type Seq<a, -A: Kind(a)> is Kind(a):
  Stop{}
  Link{head: A, tail: Seq<a, A>}

def foldl(~a: Quant, ~A: Kind(a), ~B: Type, ~f: B -> A -> B, xs: Seq<a, A>, acc: B) -> B:
  match xs:
    case Stop{}: acc
    case Link{h,t}: foldl(~a,~A,~B,~f,t,f(acc,h))

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def keep(x: Flag) -> Flag:
  x

def xor(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: b
    case On{}: invert(b)

def parity(a: Flag, b: Flag, c: Flag) -> Flag:
  foldl(~&2,~Flag,~Flag,~xor,Link{a,Link{b,Link{c,Stop{}}}},Off{})

def pick(g: Flag) -> Flag -> Flag:
  match g:
    case Off{}: keep
    case On{}: invert

def pipeline(g: Flag, h: Flag, x: Flag) -> Flag:
  foldl(~&1,~(Flag -> Flag),~Flag,~(acc => k => k(acc)),Link{pick(g),Link{pick(h),Stop{}}},x)

def main() -> Flag:
  parity(On{},On{},On{})
