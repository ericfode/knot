# Typed lets give a list its type: +xs : List<&2,Flag> = [..] or Con{..}, then used twice.
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

def literal(f: Flag, g: Flag) -> Flag:
  +xs : List<&2,Flag> = [f,g]
  pick(head(xs),second(xs))

def consed(f: Flag, g: Flag) -> Flag:
  +introduced : List<&2,Flag> = Con{g,[f]}
  pick(second(introduced),head(introduced))

def main() -> Flag:
  literal(On{},On{})
