# All-variable match on a let binder.
type Flag is Data:
  Off{}
  On{}

def id(x: Flag) -> Flag:
  x

def f(x: Flag) -> Flag:
  y = id(x)
  match y:
    case z: z

def main() -> Flag:
  f(On{})
