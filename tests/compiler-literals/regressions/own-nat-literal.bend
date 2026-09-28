# Without Base, `2n` spells this book's own Nat, which Knot does not install.
type Nat is Data:
  Zero{}
  Succ{pred: Nat}

type Answer is Type:
  No{}
  Yes{}

def pick(n: Nat) -> Answer:
  match n:
    case Zero{}: No{}
    case Succ{p}: Yes{}

def main() -> Answer:
  pick(2n)
