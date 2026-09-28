type Flag is Type:
  Off{}
  On{}

type Cell is Type:
  Cell{value: Flag}

def take(x: Cell) -> Flag:
  Cell{value} =
  value

def main() -> Flag:
  take(Cell{On{}})
