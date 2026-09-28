# Operator sugar over U32: (a + b : U32) is U32.add(a, b); < is U32.is_lt.
import Base

type Answer is Type:
  No{}
  Yes{}

type Op is Type:
  Carry{}
  Borrow{}
  Below{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def check(o: Op) -> Answer:
  match o:
    case Carry{}: verdict(U32.is_eq((4294967295 + 1 : U32), 0))
    case Borrow{}: verdict(U32.is_eq((0 - 1 : U32), 4294967295))
    case Below{}: verdict((4294967295 < 0 : U32))

def main() -> Answer:
  check(Carry{})
