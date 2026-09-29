# A literal after a name in a call: the seed reads two arguments.
import Base

type Answer is Type:
  No{}
  Yes{}

def two(a: U32, b: U32) -> Answer:
  Yes{}

def f(x: U32) -> Answer:
  two(x 3)

def main() -> Answer:
  f(0)
