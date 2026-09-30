type Signal is Data:
  Low{}
  High{}

type Crate<-A: Data> is Data:
  Pack{item: A}

def keep
(-A: Data, x: A) -> A:
  x

def main() -> Signal:
  High{}
