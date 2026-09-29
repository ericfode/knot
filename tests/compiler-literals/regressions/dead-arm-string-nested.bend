import Base

# `SCon{'a', SNil{}}` spells "a" again through nested columns, so its body is never checked.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def pick(s: String) -> U32:
  match s:
    case "a": 0
    case SCon{'a', SNil{}}: 'x'
    case _: 1

def main() -> Answer:
  answer(U32.is_eq(pick("a"), 0))
