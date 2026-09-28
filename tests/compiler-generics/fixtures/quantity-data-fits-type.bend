# Data fits Kind(&1): a Data element type instantiates an affine quantity.
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

def one(x: Flag) -> Flag:
  head_or(&1, Flag, Link{x, End{}}, Off{})

def main() -> Flag:
  one(On{})
