type Flag is Data:
  Off{}
  On{}

type Seq<a, -A: Kind(a)> is Kind(a):
  End{}
  Link{head: A, tail: Seq<a,A>}

def same(a, -A: Kind(a), xs: Seq<a <&> &0,A>) -> Seq<&0,A>:
  xs

def head_or(a, -A: Kind(a), xs: Seq<a,A>, fallback: A) -> A:
  match xs:
    case End{}:
      fallback
    case Link{head,tail}:
      head

def round(x: Flag) -> Flag:
  head_or(&0,Flag,same(&1,Flag,Link{x,End{}}),Off{})

def main() -> Flag:
  round(On{})
