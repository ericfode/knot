type Flag is Data:
  Off{}
  On{}

def f(x: Flag, y: Flag) -> Flag:
  match x y:
    case a.b On{}: a.b
    case _ _: Off{}

def main() -> Flag:
  f(On{}, On{})
