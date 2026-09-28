import ./lib/flag.bend as A
import ./lib/flag.bend as B

type Light is Type:
  Dark{}
  Lit{}

def see(x: A.Flag) -> Light:
  match x:
    case A.Off{}: Dark{}
    case A.On{}: Lit{}

def main() -> Light:
  see(B.flip(B.Off{}))
