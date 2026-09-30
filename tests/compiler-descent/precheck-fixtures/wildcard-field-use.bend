type Flag is Data:
  Off{}
  On{}

type Cell is Data:
  Cell{v: Flag}

def f(c: Cell) -> Flag:
  match c:
    case Cell{_}: _

def main() -> Flag:
  f(Cell{On{}})
