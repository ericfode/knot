type Flag is Data:
  Off{}
  On{}

def main() -> Flag:
  x : Flag = Off{}
  f : Flag -> Flag = x => x
  f(On{})
