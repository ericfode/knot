type Flag is Data:
  Off{}
  On{}

def keep(f: Flag -> Flag) -> Flag:
  f(Off{})

def main() -> Flag:
  keep(x => On{})
