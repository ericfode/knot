type Flag is Data:
  Off{}
  On{}

type Cell is Data:
  Cell{value: Flag}

def f(-a: Flag ~b: Flag -c: Flag) -> Flag:
  On{}
