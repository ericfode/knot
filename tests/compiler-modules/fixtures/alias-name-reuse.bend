import ./lib/flag.bend as F

type F is Type:
  Dark{}
  Lit{}

def see(x: F.Flag) -> F:
  match x:
    case F.Off{}: Dark{}
    case F.On{}: Lit{}

def main() -> F:
  F : F.Flag = F.On{}
  see(F.flip(F))
