type Flag is Data:
  Off{}
  On{}

def same(xs: +Seq<&1,Flag>) -> Flag:
  On{}

type Seq<a, -A: Kind(a)> is Kind(a):
  End{}
  Link{head: A, tail: Seq<a,A>}

def main() -> Flag:
  On{}
