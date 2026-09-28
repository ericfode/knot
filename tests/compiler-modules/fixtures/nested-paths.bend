import ./lib/flag.bend as F
import ./lib/deep/a/b/leaf.bend as Leaf

type Light is Type:
  Dark{}
  Lit{}

def see(x: F.Flag) -> Light:
  match x:
    case F.Off{}: Dark{}
    case F.On{}: Lit{}

def main() -> Light:
  see(Leaf.twice(F.On{}))
