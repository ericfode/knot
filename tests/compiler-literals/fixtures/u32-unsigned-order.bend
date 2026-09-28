# U32 comparison is unsigned: 2147483648 (bit 31 set) is above 0.
import Base

type Answer is Type:
  No{}
  Yes{}

type Mark is Type:
  Bottom{}
  Middle{}
  Top{}

type Order is Type:
  Less{}
  Same{}
  More{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def order(c: Cmp) -> Order:
  match c:
    case LT{}: Less{}
    case EQ{}: Same{}
    case GT{}: More{}

def value(m: Mark) -> U32:
  match m:
    case Bottom{}: 0
    case Middle{}: 2147483648
    case Top{}: 4294967295

def compare(a: Mark, b: Mark) -> Order:
  order(U32.cmp(value(a), value(b)))

def below(a: Mark, b: Mark) -> Answer:
  verdict(U32.is_lt(value(a), value(b)))

def main() -> Order:
  compare(Middle{}, Bottom{})
