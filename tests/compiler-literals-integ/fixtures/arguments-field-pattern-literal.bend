# And between the fields of a constructor pattern: `Two{a 4}` binds a and matches 4.
import Base

type Answer is Type:
  No{}
  Yes{}

type Two is Data:
  Two{a: U32, b: U32}

def f(x: Two) -> Answer:
  match x:
    case Two{a 4}: Yes{}
    case _: No{}

def main() -> Answer:
  f(Two{1, 4})
