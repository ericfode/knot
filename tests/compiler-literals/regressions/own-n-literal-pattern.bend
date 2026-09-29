# The spelling is by constructor, not by type name: here the type is N.
type Answer is Type:
  No{}
  Yes{}

type N is Data:
  Zero{}
  Succ{pred: N}

def two(n: N) -> Answer:
  match n:
    case 2n: Yes{}
    case _: No{}

def main() -> Answer:
  two(Succ{Succ{Zero{}}})
