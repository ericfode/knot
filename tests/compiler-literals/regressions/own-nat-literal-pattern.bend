# Without Base, `2n` spells this book's own Succ and Zero.
type Answer is Type:
  No{}
  Yes{}

type Nat is Data:
  Zero{}
  Succ{pred: Nat}

def two(n: Nat) -> Answer:
  match n:
    case 2n: Yes{}
    case _: No{}

def main() -> Answer:
  two(Succ{Succ{Zero{}}})
