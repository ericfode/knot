# The seed accepts this: `Flag` names no type in this file, only in the module imported as L. The
# checker sees the imported type spelled with its module and cannot tell the two apart, so it
# stays unsupported (D4) rather than reading a fresh name as a type.
import ./promoted-type-imported/lib.bend as L

type Answer is Type:
  No{}
  Yes{}

def f(x: L.Flag) -> Answer:
  match x:
    case L.Off{}: Yes{}
    case +Flag: No{}

def main() -> Answer:
  f(L.On{})
