# A literal after a variable column: the row reads `v` and then the literal.
import Base

type Answer is Type:
  No{}
  Yes{}

def f(a: Answer, n: U32) -> Answer:
  match a n:
    case v 0: Yes{}
    case _ _: No{}

def main() -> Answer:
  f(No{}, 0)
