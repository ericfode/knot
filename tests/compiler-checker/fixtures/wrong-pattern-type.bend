type Flag is Type:
  Off{}
  On{}
type Other is Type:
  OtherTag{}
def f(x: Flag) -> Flag:
  match x:
    case OtherTag{}: On{}
def main() -> Flag:
  f(Off{})
