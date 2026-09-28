import Base

# `3n+q` precedes `1n+p` and is reachable, so its ill-typed body is checked.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def pick(n: Nat) -> U32:
  match n:
    case 0n: 0
    case 3n+q: 'x'
    case 1n+p: 1

def main() -> Answer:
  answer(U32.is_eq(pick(3n), 1))
