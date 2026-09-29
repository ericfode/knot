import ./lib/left.bend as L

type Light is Type:
  Dark{}
  Lit{}

def see(x: L.F.Flag) -> Light:
  match x:
    case L.F.Off{}: Dark{}
    case L.F.On{}: Lit{}

def main() -> Light:
  see(L.left(L.F.Off{}))
