# A Nat offset in a row of several columns: the seed accepts it too.
import Base

type Answer is Type:
  No{}
  Yes{}

def f(n: Nat, a: Answer) -> Answer:
  match n a:
    case 1n+p No{}: Yes{}
    case _ _: No{}

def main() -> Answer:
  f(3n, No{})
