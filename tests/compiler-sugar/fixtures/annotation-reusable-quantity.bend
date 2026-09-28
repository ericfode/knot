# A reusable typed let whose annotation is the affine List<&1,Flag>.
import Base

type Flag is Data:
  Off{}
  On{}

def head(xs: List<&2,Flag>) -> Flag:
  match xs:
    case Nil{}: Off{}
    case Con{h,t}: h

def second(xs: List<&2,Flag>) -> Flag:
  match xs:
    case Nil{}: Off{}
    case Con{h,t}: head(t)

def pick(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def run(f: Flag, g: Flag) -> Flag:
  +xs : List<&1,Flag> = [f,g]
  pick(head(xs),second(xs))

def main() -> Flag:
  run(On{},On{})
