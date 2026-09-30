type Flag is Data:
  Off{}
  On{}

type P is Type:
  P{a: Flag, b: Flag}

def f(x: Flag, y: Flag) -> Flag:
  match x y:
    case On {} v: v
    case _ _: Off{}

def main() -> Flag:
  f(On{}, On{})
