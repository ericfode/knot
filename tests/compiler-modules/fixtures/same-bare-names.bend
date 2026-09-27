import ./lib/flag.bend as M

type Flag is Type:
  Off{}
  On{}

def flip(x: Flag) -> Flag:
  x

def main() -> Flag:
  flip(On{})
