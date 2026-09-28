type Flag is Data:
  Off{}
  On{}

def pick(-ghost: Flag, x: Flag, y: Flag) -> Flag:
  x

def run(x: Flag) -> Flag:
  f = pick(x)
  f(x, Off{})

def main() -> Flag:
  run(On{})
