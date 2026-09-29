# The same rule for a promoted binder in a constructor's fields.
type Flag is Data:
  Off{}
  On{}

type Cell is Data:
  Cell{v: Flag}

def f(c: Cell) -> Flag:
  match c:
    case Cell{+Flag}: On{}

def main() -> Flag:
  f(Cell{On{}})
