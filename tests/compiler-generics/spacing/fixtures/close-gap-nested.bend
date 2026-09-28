type Flag is Data:
  Off{}
  On{}

type Seq<a, -A: Kind(a)> is Kind(a):
  End{}
  Link{head: A, tail: Seq<a,A>}

def outer(xs: Seq<&2,Seq<&2,Flag> >) -> Flag:
  On{}

def main() -> Flag:
  outer(End{})
