import ./x.bend as A
import .//x.bend as B

type Light is Type:
  Dark{}
  Lit{}

def see(x: A.Flag) -> Light:
  match x:
    case A.Off{}: Dark{}
    case A.On{}: Lit{}

def main() -> Light:
  see(B.On{})
