type Flag is Data:
  Off{}
  On{}

type Pair is Data:
  Pair{left: Flag, right: Flag}

def swap(a: Flag, b: Flag) -> Pair:
  f : Flag -> Pair = x => Pair{b,a}
  f(Off{})

def main() -> Pair:
  swap(Off{},On{})
