type Flag is Data:
  Off{}
  On{}

def keep(k: Flag) -> Flag -> Flag:
  x => k

def main() -> Flag:
  keep(On{})(Off{})
