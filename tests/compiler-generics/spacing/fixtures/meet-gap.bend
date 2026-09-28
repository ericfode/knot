type Flag is Data:
  Off{}
  On{}

type Pair<a, b, -A: Kind(a), -B: Kind(b)> is Kind(a < & > b):
  Pair{fst: A, snd: B}

def main() -> Flag:
  On{}
