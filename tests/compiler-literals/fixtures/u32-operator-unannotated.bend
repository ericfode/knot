# Negative: an operator without a (.. : T) annotation is refused.
import Base

type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def main() -> Answer:
  verdict(U32.is_eq(4294967295 + 1, 0))
