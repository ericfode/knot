# An erased let binds its name below it too.
type Flag is Data:
  Off{}
  On{}

def f(+x: Flag) -> Flag:
  -Flag = x
  y : Flag = x
  On{}

def main() -> Flag:
  f(On{})
