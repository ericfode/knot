# Seq<&2, Flag> does not fit Seq<&1, Flag>: datatype quantities are invariant.
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

def make(x: Flag) -> Seq<&2, Flag>:
  Link{x, End{}}

def once(xs: Seq<&1, Flag>) -> Flag:
  head_or(&1, Flag, xs, Off{})

def main() -> Flag:
  once(make(On{}))
