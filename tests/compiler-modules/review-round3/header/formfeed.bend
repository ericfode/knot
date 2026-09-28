import./lib/flag.bend as F
import ./lib/other.bend as G

type Light is Type:
  Dark{}
  Lit{}

def see(x: F.Flag) -> Light:
  match x:
    case F.Off{}: Dark{}
    case F.On{}: Lit{}

def main() -> Light:
  see(F.flip(F.Off{}))

def other() -> G.Flag:
  G.Off{}
