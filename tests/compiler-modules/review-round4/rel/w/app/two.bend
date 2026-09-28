import ./m/flag.bend as A
import ../../w/app/m/flag.bend as B

type Light is Type:
  Dark{}
  Lit{}

def see(x: B.Flag) -> Light:
  match x:
    case B.Off{}: Dark{}
    case B.On{}: Lit{}

def main() -> Light:
  see(A.flip(A.Off{}))
