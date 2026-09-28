# U32.from_nat(U32.to_nat(1048576)): the compiler's maximum output budget
# crosses the Nat representation and back (DEC-5).
import Base

type Answer is Type:
  No{}
  Yes{}

type Size is Type:
  Budget{}
  Short{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def word(s: Size) -> U32:
  match s:
    case Budget{}: 1048576
    case Short{}: 1048575

def roundtrip(s: Size) -> Answer:
  verdict(U32.is_eq(U32.from_nat(U32.to_nat(word(s))),1048576))

def main() -> Answer:
  roundtrip(Budget{})
