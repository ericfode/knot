import Base

# A catch-all without `+` leaves its scrutinee affine: two uses are a reuse.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def default(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case x: answer(Nat.is_eq(Nat.add(n, n), 4n))

def main() -> Answer:
  default(2n)
