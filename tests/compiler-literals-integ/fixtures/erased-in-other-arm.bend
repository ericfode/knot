# A let binds its name in its own body only: the other arm's live let of that name binds nothing.
type Flag is Data:
  Off{}
  On{}

def f(+x: Flag) -> Flag:
  match x:
    case Off{}:
      -a.b : Flag = x
      On{}
    case On{}:
      a.b : Flag = x
      On{}

def main() -> Flag:
  f(On{})
