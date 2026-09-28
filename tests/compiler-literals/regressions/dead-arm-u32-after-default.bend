import Base

# A literal arm after a binder is unreachable, so its ill-typed body is never checked.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def pick(x: U32) -> U32:
  match x:
    case y: 0
    case 3: "s"

def main() -> Answer:
  answer(U32.is_eq(pick(3), 0))
