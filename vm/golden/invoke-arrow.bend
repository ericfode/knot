type Flag is Data:
  Off{}
  On{}

def feed(x: Flag, f: Flag -> Flag) -> Flag:
  f(x)

def main() -> Flag:
  feed(On{},x => x)
