import Base

# The second `case 'a'` is unreachable, so its ill-typed body is never checked.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def pick(c: Char) -> U32:
  match c:
    case 'a': 0
    case 'a': "no"
    case _: 1

def main() -> Answer:
  answer(U32.is_eq(pick('a'), 0))
