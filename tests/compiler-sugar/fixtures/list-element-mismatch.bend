# A list literal whose second element has another type.
import Base

type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def head(xs: List<&2,Flag>) -> Flag:
  match xs:
    case Nil{}: Off{}
    case Con{h,t}: h

def run(f: Flag) -> Flag:
  head([f,Red{}])

def main() -> Flag:
  run(On{})
