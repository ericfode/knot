type Flag is Data:
  Off{}
  On{}

def second(a: Flag, b: Flag) -> Flag:
  match a b:
    case Off{} _: _
    case On{} x: x

def main() -> Flag:
  second(Off{}, On{})
