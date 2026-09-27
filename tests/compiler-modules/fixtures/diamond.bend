import ./lib/left.bend as L
import ./lib/right.bend as R
import ./lib/flag.bend as F

type Light is Type:
  Dark{}
  Lit{}

def see(x: F.Flag) -> Light:
  match x:
    case F.Off{}: Dark{}
    case F.On{}: Lit{}

def main() -> Light:
  see(R.right(L.left(F.Off{})))
