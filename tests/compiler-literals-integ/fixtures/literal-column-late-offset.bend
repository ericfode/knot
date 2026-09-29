# A Nat offset in a later column of a whitespace-separated row.
import Base

type Answer is Type:
  No{}
  Yes{}

def f(a: Answer, n: Nat) -> Answer:
  match a n:
    case No{} 1n+p: Yes{}
    case _ _: No{}

def main() -> Answer:
  f(No{}, 3n)
