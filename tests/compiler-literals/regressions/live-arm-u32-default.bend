import Base

# The catch-all is reachable, though shadowed on the `5` path, so its body is checked.
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
    case _: 'q'

def main() -> Answer:
  answer(U32.is_eq(pick(5), 0))
