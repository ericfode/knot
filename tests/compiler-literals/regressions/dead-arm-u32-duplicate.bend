import Base

# The second `case 5` is unreachable, so the seed never checks its body.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def pick(x: U32) -> U32:
  match x:
    case 5: 0
    case 5: 'q'
    case _: 2

def main() -> Answer:
  answer(U32.is_eq(pick(5), 0))
