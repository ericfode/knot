import Base

# The book's own constructor, declared before the function, is no name for a field binder.
type Answer is Type:
  No{}
  Yes{}

type Box is Type:
  Box{v: U32}

def f(b: Box) -> Answer:
  match b:
    case Box{Yes}: No{}

def main() -> Answer:
  f(Box{3})
