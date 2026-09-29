import Base

# `2n` is subsumed by `1n+p`, so its ill-typed body is never checked.
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
    case 1n+p: 1
    case 2n: 'a'

def main() -> Answer:
  answer(U32.is_eq(pick(2n), 1))
