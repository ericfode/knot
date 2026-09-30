type Signal is Data:
  Low{}
  High{}

type Crate<-A: Data>
 is Data:
  Pack{item: A}

def main() -> Signal:
  High{}
