# Without Base, `3` spells this book's own U32, which declares only Z.
type U32 is Data:
  Z{}

type Answer is Type:
  No{}
  Yes{}

def pick(n: U32) -> Answer:
  match n:
    case Z{}: Yes{}

def main() -> Answer:
  pick(3)
