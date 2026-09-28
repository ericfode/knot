import Base

# The seed checks the pattern of an unreachable arm: a Char literal spells no U32.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def pick(x: U32) -> U32:
  match x:
    case _: 0
    case 'a': 1

def main() -> Answer:
  answer(U32.is_eq(pick(0), 0))
