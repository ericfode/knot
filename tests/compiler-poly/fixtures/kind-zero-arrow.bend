# Kind(&0) at an arrow: size counts a Seq<&0,Flag -> Flag> whose closures are built live and never called.
type Flag is Data:
  Off{}
  On{}

type Parity is Data:
  Even{}
  Odd{}

type Seq<a, -A: Kind(a)> is Kind(a):
  Stop{}
  Link{head: A, tail: Seq<a, A>}

def flip(p: Parity) -> Parity:
  match p:
    case Even{}: Odd{}
    case Odd{}: Even{}

def size(a, -A: Kind(a), xs: Seq<a, A>) -> Parity:
  match xs:
    case Stop{}: Even{}
    case Link{h,t}: flip(size(a,A,t))

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def unused(g: Flag) -> Seq<&0,Flag -> Flag>:
  match g:
    case Off{}: Link{invert,Stop{}}
    case On{}: Link{invert,Link{y => invert(y),Stop{}}}

def zero(g: Flag) -> Parity:
  size(&0,Flag -> Flag,unused(g))

def main() -> Parity:
  zero(Off{})
