# Without the marker a type's name is an ordinary binder, in a pattern, an erased let and a let.
type Flag is Data:
  Off{}
  On{}

def pattern(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case Flag: Off{}

def erased(+x: Flag) -> Flag:
  -Flag = x
  x

def plain(+x: Flag) -> Flag:
  Flag = x
  On{}

def main() -> Flag:
  plain(erased(pattern(On{})))
