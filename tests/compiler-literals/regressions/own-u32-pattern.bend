# Without Base, `3` spells a U32 word, which Knot does not model.
type U32 is Data:
  Z{}

type Answer is Type:
  No{}
  Yes{}

def three(n: U32) -> Answer:
  match n:
    case 3: Yes{}
    case _: No{}

def main() -> Answer:
  three(Z{})
