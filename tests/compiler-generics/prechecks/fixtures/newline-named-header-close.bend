type Signal is Data:
  Low{}
  High{}

type Crate<-A: Signal
>
is Data:
  Pack{item: A}

def main() -> Signal:
  High{}
