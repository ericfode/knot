type Flag is Data:
  Off{}
  On{}

type Pair<a, b, -A: Kind(a), -B: Kind(b)> is Kind(a <&>b):
  Pair{fst: A, snd: B}

type Twin<a, b, -A: Kind(a), -B: Kind(b)> is Kind(a<&>b):
  Twin{fst: A, snd: B}

def first(p: Pair<&2,&2,Flag,Flag>) -> Flag:
  match p:
    case Pair{x,y}:
      x

def keep(x: Flag) -> Flag:
  first(Pair{x,Off{}})

def main() -> Flag:
  keep(On{})
