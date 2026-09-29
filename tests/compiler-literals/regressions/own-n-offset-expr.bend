# Without Base, `2n+n` against N spells N's own Succ twice.
type Answer is Type:
  No{}
  Yes{}

type N is Data:
  Zero{}
  Succ{pred: N}

def up(n: N) -> N:
  2n+n

def positive(n: N) -> Answer:
  match n:
    case Zero{}: No{}
    case Succ{p}: Yes{}

def main() -> Answer:
  positive(up(Zero{}))
