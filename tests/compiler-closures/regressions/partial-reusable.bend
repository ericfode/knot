type Flag is Data:
  Off{}
  On{}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: Off{}
    case On{}: b

def use(+x: Flag, y: Flag) -> Flag:
  both(x, both(x, y))

def run(x: Flag) -> Flag:
  f = use(x)
  f(On{})

def main() -> Flag:
  run(On{})
