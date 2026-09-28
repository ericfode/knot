type Flag is Data:
  Off{}
  On{}

def keep(-w: Flag, y: Flag) -> Flag:
  y

def hold(-w: Flag) -> Flag -> Flag -> Flag:
  x => y => keep(w, y)

def main() -> Flag:
  hold(On{})(Off{})(On{})
