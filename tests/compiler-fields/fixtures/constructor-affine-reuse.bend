type Flag is Data:
  Off{}
  On{}
type Pair is Type:
  Pair{left: Flag, right: Flag}
def pair(x: Flag) -> Pair:
  Pair{x,x}
def main() -> Pair:
  pair(On{})
