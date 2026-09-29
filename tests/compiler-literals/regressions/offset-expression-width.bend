import Base

# `kn+t` is k successors around a shared t whatever k, as in the seed: a count in
# the thousands is one expression, not a recursion.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def edge(t: Nat) -> Nat:
  1364n+t

def past(t: Nat) -> Nat:
  1365n+t

def wide(t: Nat) -> Nat:
  2000n+t

def at_edge() -> Answer:
  answer(Nat.is_eq(edge(2n), 1366n))

def past_edge() -> Answer:
  answer(Nat.is_eq(past(2n), 1367n))

def wide_sum() -> Answer:
  answer(Nat.is_eq(wide(5n), 2005n))

def wide_short() -> Answer:
  answer(Nat.is_eq(wide(5n), 2004n))

def main() -> Answer:
  past_edge()
