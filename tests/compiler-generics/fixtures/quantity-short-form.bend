# Short forms: Seq<Flag> means Seq<&1, Flag>; +Seq<Flag> means Seq<&2, Flag>.
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

def once(xs: Seq<Flag>) -> Flag:
  head_or(&1, Flag, xs, Off{})

def reuse(+xs: +Seq<Flag>) -> Flag:
  head_or(&2, Flag, xs, head_or(&2, Flag, xs, Off{}))

def single(x: Flag) -> Flag:
  once(Link{x, End{}})

def double(x: Flag) -> Flag:
  reuse(Link{x, End{}})

def main() -> Flag:
  double(On{})
