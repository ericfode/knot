# U32 add, sub and mul wrap modulo 2^32.
import Base

type Answer is Type:
  No{}
  Yes{}

type Op is Type:
  Carry{}
  Borrow{}
  Square{}
  MaxSquare{}
  Near{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def result(o: Op) -> U32:
  match o:
    case Carry{}: U32.add(4294967295, 1)
    case Borrow{}: U32.sub(0, 1)
    case Square{}: U32.mul(65536, 65536)
    case MaxSquare{}: U32.mul(4294967295, 4294967295)
    case Near{}: U32.add(4294967294, 1)

def is_zero(o: Op) -> Answer:
  verdict(U32.is_eq(result(o), 0))

def is_max(o: Op) -> Answer:
  verdict(U32.is_eq(result(o), 4294967295))

def is_one(o: Op) -> Answer:
  verdict(U32.is_eq(result(o), 1))

def main() -> Answer:
  is_zero(Carry{})
