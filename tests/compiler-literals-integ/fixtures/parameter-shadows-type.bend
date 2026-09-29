# The marker is beside the point: the plain `Flag: Flag` is the same variable where a type is due.
type Flag is Data:
  Off{}
  On{}

def f(Flag: Flag) -> Flag:
  On{}

def main() -> Flag:
  f(On{})
