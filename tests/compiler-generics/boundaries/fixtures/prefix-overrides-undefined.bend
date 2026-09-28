type Flag is Data:
  Off{}
  On{}

type Seq<a, -A: Kind(a)> is Kind(a):
  End{}
  Link{head: A, tail: Seq<a,A>}

def same(xs: +Seq<Missing,Flag>) -> Seq<&2,Flag>:
  xs

def head_or(a, -A: Kind(a), xs: Seq<a,A>, fallback: A) -> A:
  match xs:
    case End{}:
      fallback
    case Link{head,tail}:
      head

def round(x: Flag) -> Flag:
  head_or(&2,Flag,same(Link{x,End{}}),Off{})

def main() -> Flag:
  round(On{})
