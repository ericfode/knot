# Negative: nine hex digits exceed the \u{..} window, whatever the value.
import Base

type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def main() -> Answer:
  verdict(U32.is_eq(Char.to_u32('\u{000000041}'), 65))
