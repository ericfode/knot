type Flag is Data:
  Off{}
  On{}

type Seq<a, -A: Kind(a)> is Kind(a):
  End{}
  Link{head: A, tail: Seq<a,A>}

def head(-a, -A: Kind(a), xs: Seq<a,A>, d: A) -> A:
  match xs:
    case End{}:
      d
    case Link{h,t}:
      h

def main() -> Flag:
  head(&2, Flag, Link{On{},End{}}, Off{})
