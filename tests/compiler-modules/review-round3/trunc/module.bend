import ./lib/big.bend as B

type Light is Type:
  Dark{}
  Lit{}

def see(x: B.Flag) -> Light:
  match x:
    case B.Off{}: Dark{}
    case B.On{}: Lit{}

def main() -> Light:
  see(B.On{})
