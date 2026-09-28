# The seed accepts a Data element type at Kind(&0) when abstract code uses it once.
type Flag is Data:
  Off{}
  On{}

type Seq<a, -A: Kind(a)> is Kind(a):
  End{}
  Link{head: A, tail: Seq<a, A>}

def head_or(a, -A: Kind(a), xs: Seq<a, A>, d: A) -> A:
  match xs:
    case End{}:
      d
    case Link{h, t}:
      h

def zero(x: Flag) -> Flag:
  head_or(&0, Flag, Link{x, End{}}, Off{})

def main() -> Flag:
  zero(On{})
