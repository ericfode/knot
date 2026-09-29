# A row wider than the match: one scrutinee, two patterns. The seed wants one pattern per scrutinee.
import Base

type Answer is Type:
  No{}
  Yes{}

def f(v: Nat) -> Answer:
  match v:
    case x y: Yes{}
    case _: No{}

def main() -> Answer:
  f(2n)
