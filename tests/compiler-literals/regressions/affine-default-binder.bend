import Base

# A field's `+` leaves its column affine: the catch-all binder may not be used twice.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def default(v: Nat) -> Answer:
  match v:
    case 1n+ +p: No{}
    case x: answer(Nat.is_eq(Nat.add(x, x), 0n))

def main() -> Answer:
  default(0n)
