import Base

# A literal arm after a binder is unreachable, so its reuse of k is never checked.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def pick(x: U32, k: U32) -> U32:
  match x:
    case y: k
    case 3: U32.add(k, k)

def main() -> Answer:
  answer(U32.is_eq(pick(3, 7), 7))
