# The same whitespace between the fields of a constructor value.
import Base

type Answer is Type:
  No{}
  Yes{}

type Two is Data:
  Two{a: U32, b: U32}

def f(x: Two) -> Answer:
  match x:
    case Two{a, b}: Yes{}

def main() -> Answer:
  f(Two{3 4})
