import ./m/flag.bend as A

type Light is Type:
  Dark{}
  Lit{}

def see(x: A.Flag) -> Light:
  match x:
    case A.Off{}: Dark{}
    case A.On{}: Lit{}

def main() -> Light:
  see(A.flip(A.Off{}))
