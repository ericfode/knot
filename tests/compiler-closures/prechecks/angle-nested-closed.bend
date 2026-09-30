type Flag is Data:
  Off{}
  On{}

type Cell is Data:
  Cell{value: Flag}

def f() -> List<List<Flag>>:
  On{}
