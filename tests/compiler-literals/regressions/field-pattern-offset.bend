import Base

# A Nat offset inside a constructor pattern is a nested pattern.
type Answer is Type:
  No{}
  Yes{}

type Cell is Data:
  Cell{value: Nat}

def inspect(c: Cell) -> Answer:
  match c:
    case Cell{1n+p}: Yes{}

def main() -> Answer:
  inspect(Cell{3n})
