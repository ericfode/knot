type Flag is Data:
  Off{}
  On{}

def f(x: Flag, y: Flag) -> Flag:
  match x y:
    case On{},
      : On{}
    case _ _: Off{}

def main() -> Flag:
  f(On{}, On{})
