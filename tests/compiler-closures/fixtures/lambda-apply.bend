# A lambda and a named definition flow into the same function-typed parameter.
type Flag is Data:
  Off{}
  On{}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def apply(f: Flag -> Flag, x: Flag) -> Flag:
  f(x)

def by_lambda(x: Flag) -> Flag:
  apply(y => invert(y), x)

def by_name(x: Flag) -> Flag:
  apply(invert, x)

def main() -> Flag:
  by_lambda(On{})
