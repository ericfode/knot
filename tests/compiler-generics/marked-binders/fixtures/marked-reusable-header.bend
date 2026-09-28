type Flag is Data:
  Off{}
  On{}

type Seq<a, -A: Kind(a)> is Kind(a):
  End{}
  Link{head: A, tail: Seq<a,A>}

type Box<+a, -A: Kind(a)> is Kind(a):
  Box{value: A}

def main() -> Flag:
  On{}
