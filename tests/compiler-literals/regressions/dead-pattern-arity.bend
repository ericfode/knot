import Base

# The seed checks the pattern of an unreachable arm: `Succ` has one field.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def pick(n: Nat) -> U32:
  match n:
    case _: 0
    case Succ{a, b}: 1

def main() -> Answer:
  answer(U32.is_eq(pick(0n), 0))
