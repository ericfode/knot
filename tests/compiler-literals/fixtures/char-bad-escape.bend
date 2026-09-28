# Negative: \q is not an escape (control: char-escapes).
import Base

type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def main() -> Answer:
  verdict(U32.is_eq(Char.to_u32('\q'), 65))
