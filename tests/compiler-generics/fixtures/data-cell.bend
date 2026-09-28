# A Data-kinded generic over a Data parameter is itself Data and may be reused.
type Flag is Data:
  Off{}
  On{}

type Cell<-A: Data> is Data:
  Cell{value: A}

def get(-A: Data, c: Cell<A>) -> A:
  match c:
    case Cell{v}:
      v

def both(x: Flag, y: Flag) -> Flag:
  match x:
    case Off{}:
      Off{}
    case On{}:
      y

def twice(+c: Cell<Flag>) -> Flag:
  both(get(Flag, c), get(Flag, c))

def hold(x: Flag) -> Flag:
  twice(Cell{x})

def main() -> Flag:
  hold(On{})
