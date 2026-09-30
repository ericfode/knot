type Flag is Data:
  Off{}
  On{}

type Shape is Type:
  Dot {}
  Line{a: Flag, b: Flag}

def tip(s: Shape) -> Flag:
  match s:
    case Dot{}: Off{}
    case Line{a, b}: b

def f(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: tip(Line{On{}, b})
    case Off{}: tip(Dot{})

def main() -> Flag:
  f(On{}, On{})
