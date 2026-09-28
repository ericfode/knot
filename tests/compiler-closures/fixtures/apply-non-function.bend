# A call headed by a variable whose type is not a function type.
type Flag is Data:
  Off{}
  On{}

def run(x: Flag) -> Flag:
  x(On{})

def main() -> Flag:
  run(On{})
