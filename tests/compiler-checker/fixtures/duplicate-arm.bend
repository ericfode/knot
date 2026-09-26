type Flag is Type:
  Off{}
  On{}
def f(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case Off{}: Off{}
    case On{}: On{}
def main() -> Flag:
  f(Off{})
