type Flag is Data:
  Off{}
  On{}
type Pair is Type:
  Pair{left: Flag, right: Flag}
def first(x: Pair) -> Flag:
  match x:
    case Pair{a,b}:
      a
def swap(x: Pair) -> Pair:
  match x:
    case Pair{a,b}:
      Pair{b,a}
def direct(a: Flag, b: Flag) -> Flag:
  first(Pair{a,b})
def swapped(a: Flag, b: Flag) -> Flag:
  first(swap(Pair{a,b}))
def main() -> Flag:
  swapped(Off{},On{})
