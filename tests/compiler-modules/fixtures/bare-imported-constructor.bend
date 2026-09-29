import ./lib/flag.bend as F

type Light is Type:
  Dark{}
  Lit{}

def see(x: F.Flag) -> Light:
  match x:
    case Off{}: Dark{}
    case On{}: Lit{}

def main() -> Light:
  see(F.On{})
