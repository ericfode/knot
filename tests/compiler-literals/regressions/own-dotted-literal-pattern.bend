# A dotted root type name still declares bare constructors, which `2n` spells.
type Answer is Type:
  No{}
  Yes{}

type A.T is Data:
  Zero{}
  Succ{pred: A.T}

def two(n: A.T) -> Answer:
  match n:
    case 2n: Yes{}
    case _: No{}

def main() -> Answer:
  two(Succ{Succ{Zero{}}})
