import Base

# `2n` is subsumed by `1n+p`, so its reuse of k is never checked.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def pick(n: Nat, k: U32) -> U32:
  match n:
    case 0n: k
    case 1n+p: k
    case 2n: U32.add(k, k)

def main() -> Answer:
  answer(U32.is_eq(pick(2n, 7), 7))
