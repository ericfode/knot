import Base

# A plain catch-all promotes nothing: the offset's field stays affine.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def offset(v: Nat) -> Answer:
  match v:
    case 0n: No{}
    case 1n+p: answer(Nat.is_eq(Nat.add(p, p), 4n))
    case x: No{}

def main() -> Answer:
  offset(3n)
