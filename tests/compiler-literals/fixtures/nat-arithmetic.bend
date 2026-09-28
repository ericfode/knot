# Nat arithmetic: subtraction saturates at 0n.
import Base

type Answer is Type:
  No{}
  Yes{}

type Op is Type:
  Under{}
  Over{}
  Even{}
  Sum{}
  Product{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def result(o: Op) -> Nat:
  match o:
    case Under{}: Nat.sub(3n, 5n)
    case Over{}: Nat.sub(5n, 3n)
    case Even{}: Nat.sub(5n, 5n)
    case Sum{}: Nat.add(2n, 3n)
    case Product{}: Nat.mul(0n, 9n)

def is_zero(o: Op) -> Answer:
  verdict(Nat.is_eq(result(o), 0n))

def main() -> Answer:
  is_zero(Under{})
