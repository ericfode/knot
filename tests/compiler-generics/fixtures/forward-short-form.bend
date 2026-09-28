# Negative twin of forward-generic-types: a forward Kind(a) family in short form.
type Flag is Data:
  Off{}
  On{}

def early(x: Flag, q: Wide<Flag>) -> Flag:
  x

type Wide<a, -A: Kind(a)> is Kind(a):
  There{value: A}

def main() -> Flag:
  early(On{}, There{Off{}})
