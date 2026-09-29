# The seed reads `+D` as a quantified datatype when D names a type: a promoted binder cannot be
# spelled like a type declared before it.
type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case +Flag: Off{}

def main() -> Flag:
  f(On{})
