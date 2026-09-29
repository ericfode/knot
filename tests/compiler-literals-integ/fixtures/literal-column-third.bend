# A literal in the third column of a whitespace-separated row.
import Base

type Answer is Type:
  No{}
  Yes{}

def f(a: Answer, b: Answer, n: U32) -> Answer:
  match a b n:
    case No{} No{} 0: Yes{}
    case _ _ _: No{}

def main() -> Answer:
  f(No{}, No{}, 0)
