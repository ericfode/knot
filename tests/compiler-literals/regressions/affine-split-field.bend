import Base

# A field bound without `+` is affine even beside a promoted row.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def offset(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 1n: No{}
    case 1n+p: answer(Nat.is_eq(Nat.add(p, p), 2n))

def main() -> Answer:
  offset(2n)
