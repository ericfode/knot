type Flag is Data:
  Off{}
  On{}

type Cell is Data:
  Cell{value: Flag}

def f(x: List<(Flag -> Flag)>) -> Flag:
  On{}
