# A + lambda binder whose type is a function type: function types are Type, never Data.
type Flag is Data:
  Off{}
  On{}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def lift(h: (Flag -> Flag) -> Flag) -> Flag:
  h(invert)

def main() -> Flag:
  lift(+g => g(g(On{})))
