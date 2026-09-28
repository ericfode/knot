# size at &2 with an arrow element type: Flag -> Flag is Type, not Kind(&2).
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

def keep(x: Flag) -> Flag:
  x

def apply_all(fs: Seq<&1,Flag -> Flag>, x: Flag) -> Flag:
  match fs:
    case Stop{}: x
    case Link{f,rest}: apply_all(rest,f(x))

def steps(g: Flag) -> Seq<&1,Flag -> Flag>:
  match g:
    case Off{}: Link{invert,Stop{}}
    case On{}: Link{invert,Link{y => keep(y),Stop{}}}

def closures(g: Flag) -> Parity:
  size(&2,Flag -> Flag,steps(g))

def flags(g: Flag, h: Flag) -> Seq<&2,Flag>:
  match g:
    case Off{}: Link{h,Stop{}}
    case On{}: Link{On{},Link{h,Stop{}}}

def data(g: Flag, h: Flag) -> Parity:
  size(&2,Flag,flags(g,h))

def run(g: Flag, x: Flag) -> Flag:
  apply_all(steps(g),x)

def main() -> Parity:
  closures(On{})
