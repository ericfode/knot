type Flag is Data:
  Off{}
  On{}

def f(x: T) -> Flag:
  x

def T() -> Type:
  Flag

def main() -> Flag:
  f(On{})
