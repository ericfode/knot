type Signal is Data:
  Low{}
  High{}

type Crate<-q: Quant, -A: Kind(q)
>
is Kind(q):
  Pack{item: A}

def main() -> Signal:
  High{}
