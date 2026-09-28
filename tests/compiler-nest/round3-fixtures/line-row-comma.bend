type Flag is Data:
  Off{}
  On{}

type Pair is Type:
  Pair{l: Flag, r: Flag}

def f(x: Flag, y: Flag) -> Flag:
  match x y:
    case On{},
      On{}: On{}
    case _ _: Off{}

def main() -> Flag:
  f(On{}, On{})
