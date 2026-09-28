# Without Base, `1n+n` against the book's own Nat spells its own Succ.
type Answer is Type:
  No{}
  Yes{}

type Nat is Data:
  Zero{}
  Succ{pred: Nat}

def up(n: Nat) -> Nat:
  1n+n

def positive(n: Nat) -> Answer:
  match n:
    case Zero{}: No{}
    case Succ{p}: Yes{}

def main() -> Answer:
  positive(up(Zero{}))
