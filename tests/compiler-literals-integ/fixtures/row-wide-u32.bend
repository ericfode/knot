# The same over a U32 scrutinee.
import Base

type Answer is Type:
  No{}
  Yes{}

def f(v: U32) -> Answer:
  match v:
    case _ _: Yes{}
    case _: No{}

def main() -> Answer:
  f(2)
