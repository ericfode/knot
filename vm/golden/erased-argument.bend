type Flag is Data:
  Off{}
  On{}

def keep(-x: Flag, y: Flag) -> Flag:
  y

def main() -> Flag:
  keep(Off{},On{})
