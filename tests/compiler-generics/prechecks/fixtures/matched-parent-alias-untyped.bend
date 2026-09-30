type Signal is Data:
  Low{}
  High{}

type Crate<-A: Data> is Data:
  Pack{item: A}

def echo(-A: Data, x: Crate<A>) -> Crate<A>:
  match x:
    case Pack{item}:
      y = x
      y

def finish(x: Crate<Signal>) -> Signal:
  match x:
    case Pack{item}: item

def main() -> Signal:
  finish(echo(Signal,Pack{High{}}))
