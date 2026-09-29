# A pattern variable binds its name in its arm's body.
type Flag is Data:
  Off{}
  On{}

def f(+x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case Flag:
      y : Flag = x
      On{}

def main() -> Flag:
  f(On{})
