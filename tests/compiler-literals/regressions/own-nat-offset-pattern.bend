# Without Base, `1n+p` spells this book's own Succ.
type Answer is Type:
  No{}
  Yes{}

type Nat is Data:
  Zero{}
  Succ{pred: Nat}

def positive(n: Nat) -> Answer:
  match n:
    case 1n+p: Yes{}
    case _: No{}

def main() -> Answer:
  positive(Succ{Zero{}})
