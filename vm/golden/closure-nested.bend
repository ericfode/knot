type Flag is Data:
  Off{}
  On{}

def keep(k: Flag) -> Flag -> Flag -> Flag:
  x => y => k

def main() -> Flag:
  keep(On{})(Off{})(Off{})
