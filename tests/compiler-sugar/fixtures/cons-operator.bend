# The cons operator h <> t builds a Base List.
import Base

type Flag is Data:
  Off{}
  On{}

def head(xs: List<&2,Flag>) -> Flag:
  match xs:
    case Nil{}: Off{}
    case Con{h,t}: h

def run(f: Flag) -> Flag:
  head(f <> [])

def main() -> Flag:
  run(On{})
