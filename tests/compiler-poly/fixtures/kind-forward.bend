# The List.reverse shape: rev forwards a and A to rev_go; called at &2 (result reused with +) and at &1 arrows.
type Flag is Data:
  Off{}
  On{}

type Seq<a, -A: Kind(a)> is Kind(a):
  Stop{}
  Link{head: A, tail: Seq<a, A>}

def rev_go(a, -A: Kind(a), xs: Seq<a, A>, acc: Seq<a, A>) -> Seq<a, A>:
  match xs:
    case Stop{}: acc
    case Link{h,t}: rev_go(a,A,t,Link{h,acc})

def rev(a, -A: Kind(a), xs: Seq<a, A>) -> Seq<a, A>:
  rev_go(a,A,xs,Stop{})

def first(xs: Seq<&2,Flag>) -> Flag:
  match xs:
    case Stop{}: Off{}
    case Link{h,t}: h

def last(xs: Seq<&2,Flag>) -> Flag:
  match xs:
    case Stop{}: Off{}
    case Link{h,t}:
      match t:
        case Stop{}: h
        case Link{h2,t2}: h2

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def keep(x: Flag) -> Flag:
  x

def both(x: Flag, y: Flag) -> Flag:
  match x:
    case Off{}: Off{}
    case On{}: y

def ends(a: Flag, b: Flag) -> Flag:
  +ys = rev(&2,Flag,Link{a,Link{b,Stop{}}})
  both(first(ys),last(ys))

def front(a: Flag, b: Flag) -> Flag:
  first(rev(&2,Flag,Link{a,Link{b,Stop{}}}))

def call_first(fs: Seq<&1,Flag -> Flag>, x: Flag) -> Flag:
  match fs:
    case Stop{}: x
    case Link{f,t}: f(x)

def arrows(g: Flag, x: Flag) -> Flag:
  call_first(rev(&1,Flag -> Flag,Link{invert,Link{y => both(g,y),Stop{}}}),x)

def main() -> Flag:
  front(On{},Off{})
