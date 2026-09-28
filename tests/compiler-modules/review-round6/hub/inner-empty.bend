import ./lib//flag.bend as Y

type Light is Type:
  Dark{}
  Lit{}

def see(x: Y.Flag) -> Light:
  match x:
    case Y.Off{}: Dark{}
    case Y.On{}: Lit{}

def main() -> Light:
  see(Y.flip(Y.Off{}))
