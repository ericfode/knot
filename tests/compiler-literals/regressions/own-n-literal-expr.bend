# Without Base, `2n` against N spells N's own Succ and Zero.
type Answer is Type:
  No{}
  Yes{}

type N is Data:
  Zero{}
  Succ{pred: N}

def two() -> N:
  2n

def positive(n: N) -> Answer:
  match n:
    case Zero{}: No{}
    case Succ{p}: Yes{}

def main() -> Answer:
  positive(two())
