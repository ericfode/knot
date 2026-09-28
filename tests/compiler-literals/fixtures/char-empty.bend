# Negative: '' is not a Char literal (control: char-lexer-traps).
import Base

type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def main() -> Answer:
  verdict(U32.is_eq(Char.to_u32(''), 65))
