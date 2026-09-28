# Without Base, `0n` spells this book's own Zero, which Knot does not interpret.
type Answer is Type:
  No{}
  Yes{}

type Nat is Data:
  Zero{}
  Succ{pred: Nat}

def zero(n: Nat) -> Answer:
  match n:
    case 0n: Yes{}
    case _: No{}

def main() -> Answer:
  zero(Zero{})
