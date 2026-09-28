# U32 shifts by a Nat count: bits leave at width 32, and shr is logical.
import Base

type Answer is Type:
  No{}
  Yes{}

type Op is Data:
  HighBit{}
  PastWidth{}
  Drain{}
  Logical{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def result(o: Op) -> U32:
  match o:
    case HighBit{}: U32.shln(1, 31n)
    case PastWidth{}: U32.shln(1, 32n)
    case Drain{}: U32.shrn(4294967295, 32n)
    case Logical{}: U32.shrn(2147483648, 31n)

def expected(o: Op) -> U32:
  match o:
    case HighBit{}: 2147483648
    case PastWidth{}: 0
    case Drain{}: 0
    case Logical{}: 1

def exact(+o: Op) -> Answer:
  verdict(U32.is_eq(result(o), expected(o)))

def is_zero(o: Op) -> Answer:
  verdict(U32.is_eq(result(o), 0))

def main() -> Answer:
  exact(PastWidth{})
