import Base

# A field's `+` leaves its column affine: the catch-all may not use it twice.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def default(v: Nat) -> Answer:
  match v:
    case Succ{+p}: No{}
    case _: answer(Nat.is_eq(Nat.add(v, v), 0n))

def main() -> Answer:
  default(0n)
