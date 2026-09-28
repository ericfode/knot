type Flag is Data:
  Off{}
  On{}

type Seq<a, -A: Kind(a)> is Kind(a):
  End{}
  Link{head: A, tail: Seq<a,A>}

def one(x: Flag) -> Seq<&2,Flag >:
  Link{x,End{}}

def main() -> Flag:
  On{}
