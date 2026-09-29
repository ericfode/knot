# A Char literal in a later column of a whitespace-separated row.
import Base

type Answer is Type:
  No{}
  Yes{}

def f(a: Answer, c: Char) -> Answer:
  match a c:
    case No{} 'a': Yes{}
    case _ _: No{}

def main() -> Answer:
  f(No{}, 'a')
