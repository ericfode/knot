type Signal is Data:
  Low{}
  High{}

type Crate<-A: Data> is Data:
  Pack{item: A}

def echo(-A: Data, x: A) -> A:
  y = x
  y

def main() -> Signal:
  echo(Signal,High{})
