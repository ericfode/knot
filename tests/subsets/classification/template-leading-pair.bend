type Flag is Data:
  Off{}
  On{}

def constant(~a: Flag, ~x: Flag) -> Flag:
  x

def main() -> Flag:
  constant(Off{},On{})
