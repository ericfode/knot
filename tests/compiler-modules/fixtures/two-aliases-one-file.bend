import ./lib/flag.bend as F
import ./lib/flag.bend as G

type Light is Type:
  Dark{}
  Lit{}

def see(x: G.Flag) -> Light:
  match x:
    case F.Off{}: Dark{}
    case G.On{}: Lit{}

def main() -> Light:
  see(G.flip(F.On{}))
