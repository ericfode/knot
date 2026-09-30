type Signal is Data:
  Low{}
  High{}

type Crate<-A: Data> is Data:
  Pack{item: A}

def echo(x: Signal) -> Signal:
  match x:
    case Low{}:
      y = x
      y
    case High{}:
      y = x
      y

def main() -> Signal:
  echo(High{})
