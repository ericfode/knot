# A literal in a row of several columns: the seed accepts this two-column match.
import Base

type Answer is Type:
  No{}
  Yes{}

def f(n: U32, a: Answer) -> Answer:
  match n a:
    case 0 No{}: Yes{}
    case _ _: No{}

def main() -> Answer:
  f(0, No{})
