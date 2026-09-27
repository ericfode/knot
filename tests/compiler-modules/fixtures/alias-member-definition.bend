import ./lib/flag.bend as F

type Light is Type:
  Dark{}
  Lit{}

def F.keep(x: F.Flag) -> F.Flag:
  x

def main() -> Light:
  Lit{}
