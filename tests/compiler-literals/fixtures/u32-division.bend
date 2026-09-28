# U32 div/mod are unsigned; division by zero yields quotient 0, remainder a.
import Base

type Answer is Type:
  No{}
  Yes{}

type Op is Data:
  HalfMax{}
  MaxRest{}
  ZeroQuotient{}
  ZeroRemainder{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def result(o: Op) -> U32:
  match o:
    case HalfMax{}: U32.div(4294967295, 2)
    case MaxRest{}: U32.mod(4294967295, 10)
    case ZeroQuotient{}: U32.div(7, 0)
    case ZeroRemainder{}: U32.mod(7, 0)

def expected(o: Op) -> U32:
  match o:
    case HalfMax{}: 2147483647
    case MaxRest{}: 5
    case ZeroQuotient{}: 0
    case ZeroRemainder{}: 7

def exact(+o: Op) -> Answer:
  verdict(U32.is_eq(result(o), expected(o)))

def is_zero(o: Op) -> Answer:
  verdict(U32.is_eq(result(o), 0))

def main() -> Answer:
  exact(ZeroQuotient{})
