# A promoted typed let binder spelled like a type.
type Flag is Data:
  Off{}
  On{}

def f(+x: Flag) -> Flag:
  +Flag : Flag = x
  On{}

def main() -> Flag:
  f(On{})
