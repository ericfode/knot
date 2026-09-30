type Signal is Data:
  Low{}
  High{}

type Crate<-A: Data> is Data:
  Pack{item: A}

type Ribbon<q, -A: Kind(q)> is Kind(q):
  End{}
  Link{head: A, tail: Ribbon<q,A>}

def keep(x: Crate
<Signal>) -> Signal:
  High{}

def main() -> Signal:
  High{}
