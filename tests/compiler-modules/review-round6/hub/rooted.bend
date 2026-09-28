import .//x.bend as X

type Light is Type:
  Dark{}
  Lit{}

def see(x: X.Flag) -> Light:
  match x:
    case X.Off{}: Dark{}
    case X.On{}: Lit{}

def main() -> Light:
  see(X.flip(X.Off{}))
