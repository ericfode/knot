# A literal in a later column of a whitespace-separated row: the seed accepts it as it accepts a
# literal in the first column.
import Base

type Answer is Type:
  No{}
  Yes{}

def f(a: Answer, n: U32) -> Answer:
  match a n:
    case No{} 0: Yes{}
    case _ _: No{}

def main() -> Answer:
  f(No{}, 0)
