# Negative twin of quantity-data-fits-type: a Type element does not fit Kind(&2).
type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

type Seq<a, -A: Kind(a)> is Kind(a):
  End{}
  Link{head: A, tail: Seq<a, A>}

def head_or(a, -A: Kind(a), xs: Seq<a, A>, d: A) -> A:
  match xs:
    case End{}:
      d
    case Link{h, t}:
      h

def unbox(-A: Type, b: Box<A>) -> A:
  match b:
    case Box{v}:
      v

def main() -> Flag:
  unbox(Flag, head_or(&2, Box<Flag>, Link{Box{On{}}, End{}}, Box{Off{}}))
