import .//lib/mid.bend as M
import ./lib/flag.bend as F

type Light is Type:
  Dark{}
  Lit{}

def see(x: F.Flag) -> Light:
  match x:
    case F.Off{}: Dark{}
    case F.On{}: Lit{}

def main() -> Light:
  see(M.mid(F.Off{}))
