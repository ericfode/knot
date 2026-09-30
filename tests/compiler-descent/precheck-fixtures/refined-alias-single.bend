type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case On{}: On{}
    case v: v

def main() -> Flag:
  f(Off{})
