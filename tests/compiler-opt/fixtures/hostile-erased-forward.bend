type Flag is Data:
  Off{}
  On{}

def keep(-x: Flag, +y: Flag) -> Flag:
  y

def helper(+x: Flag) -> Flag:
  keep(caller(x),x)

def caller(+x: Flag) -> Flag:
  helper(x)

def main() -> Flag:
  caller(On{})
