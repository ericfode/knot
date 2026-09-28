# An untyped let whose initializer is a list literal.
import Base

type Flag is Data:
  Off{}
  On{}

def head(xs: List<&2,Flag>) -> Flag:
  match xs:
    case Nil{}: Off{}
    case Con{h,t}: h

def run(f: Flag) -> Flag:
  xs = [f,Off{}]
  head(xs)

def main() -> Flag:
  run(On{})
