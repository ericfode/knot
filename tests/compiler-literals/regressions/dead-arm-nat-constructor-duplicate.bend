import Base

# The second `Zero{}` arm is unreachable, so its ill-typed body is never checked.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def pick(n: Nat) -> U32:
  match n:
    case Zero{}: 0
    case Zero{}: 'x'
    case Succ{p}: 1

def main() -> Answer:
  answer(U32.is_eq(pick(0n), 0))
