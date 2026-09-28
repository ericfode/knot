# Generic types named before their declaration: a plain family in short form,
# a Kind(a) family with every parameter spelled.
type Flag is Data:
  Off{}
  On{}

def early(x: Flag, p: Later<Flag>, q: Wide<&1, Flag>) -> Flag:
  x

type Later<-A: Type> is Type:
  Here{value: A}

type Wide<a, -A: Kind(a)> is Kind(a):
  There{value: A}

def open(-A: Type, p: Later<A>) -> A:
  match p:
    case Here{v}:
      v

def late(x: Flag, y: Flag) -> Flag:
  early(open(Flag, Here{x}), Here{On{}}, There{y})

def main() -> Flag:
  late(On{}, Off{})
