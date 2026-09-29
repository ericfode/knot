# An erased let names only itself: a live let of another dotted name is a global reference.
type Flag is Data:
  Off{}
  On{}

def f(+x: Flag) -> Flag:
  -a.b : Flag = x
  a.b.c : Flag = x
  On{}

def main() -> Flag:
  f(On{})
