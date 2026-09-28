type Flag is Data:
  Off{}
  On{}

def keep(-w: Flag, y: Flag) -> Flag:
  y

def run(x: Flag) -> Flag:
  f : Flag -> Flag = y => keep(x, y)
  f(x)

def main() -> Flag:
  run(On{})
