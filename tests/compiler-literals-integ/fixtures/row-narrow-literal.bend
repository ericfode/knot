# A row narrower than the match: two scrutinees, one pattern, and the pattern is a literal.
import Base

type Answer is Type:
  No{}
  Yes{}

def f(n: Nat, s: String) -> Answer:
  match n s:
    case 0n: Yes{}
    case _ _: No{}

def main() -> Answer:
  f(0n, "a")
