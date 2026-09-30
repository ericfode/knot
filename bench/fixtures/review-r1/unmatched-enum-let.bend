type Flag is Data:
  Off{}
  On{}

def copy(x: Flag) -> Flag:
  y = x
  y

def main() -> Flag:
  copy(On{})
