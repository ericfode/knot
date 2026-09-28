import Base

# Destructuring and rebuilding a U32 through its Base constructor.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def same(x: U32) -> U32:
  match x:
    case U32{w}: U32{w}

def main() -> Answer:
  answer(U32.is_eq(same(3), 3))
