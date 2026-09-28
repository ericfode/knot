# The spelling is by constructor, not by type name: here the type is N.
type Answer is Type:
  No{}
  Yes{}

type N is Data:
  Zero{}
  Succ{pred: N}

def positive(n: N) -> Answer:
  match n:
    case 1n+p: Yes{}
    case _: No{}

def main() -> Answer:
  positive(Succ{Zero{}})
