type Flag is Data:
  Off{}
  On{}

def f(a.b: Flag, y: Flag) -> Flag:
  match a.b y:
    case On{} _: y
    case Off{} On{}: Off{}
    case Off{} Off{}: On{}

def main() -> Flag:
  f(Off{}, Off{})
