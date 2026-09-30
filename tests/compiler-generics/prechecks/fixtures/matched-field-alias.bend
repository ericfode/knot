type Signal is Data:
  Low{}
  High{}

type Crate<-A: Data> is Data:
  Pack{item: A}

def echo(-A: Data, x: Crate<A>) -> A:
  match x:
    case Pack{item}:
      y = item
      y

def main() -> Signal:
  echo(Signal,Pack{High{}})
