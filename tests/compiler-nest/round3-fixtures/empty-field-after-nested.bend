type Flag is Data:
  Off{}
  On{}

type V is Type:

type P2 is Type:
  P2{a: Flag, b: Flag}

type Q is Type:
  Q{p: P2, v: V}

def f(q: Q) -> Flag:
  match q:
    case Q{P2{On{}, _}, _}: Off{}

def main() -> Flag:
  On{}
