import Base

# Rebuilding a U32 from its Base constructor.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def zero() -> U32:
  U32{Word.zero(32n)}

def main() -> Answer:
  answer(U32.is_eq(zero(), 0))
