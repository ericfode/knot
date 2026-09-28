type Flag is Data:
  Off{}
  On{}

type V is Type:

type P2 is Type:
  P2{a: Flag, b: Flag}

type Q is Type:
  Q{v: V, p: P2}

def f(q: Q) -> Flag:
  match q:
    case Q{_, P2{On{}, _}}: Off{}

def main() -> Flag:
  On{}
