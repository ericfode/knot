import Base

# A literal inside a constructor pattern is a nested pattern.
type Answer is Type:
  No{}
  Yes{}

type Box is Data:
  Box{value: U32}

def inspect(b: Box) -> Answer:
  match b:
    case Box{3}: Yes{}

def main() -> Answer:
  inspect(Box{3})
