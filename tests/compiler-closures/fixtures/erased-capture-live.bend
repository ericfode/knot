# A closure returns its erased capture live.
type Flag is Data:
  Off{}
  On{}

def leak(-w: Flag) -> Flag -> Flag:
  y => w

def main() -> Flag:
  leak(On{})(Off{})
