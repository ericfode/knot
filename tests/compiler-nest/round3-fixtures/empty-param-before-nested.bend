type Flag is Data:
  Off{}
  On{}

type V is Type:

type P2 is Type:
  P2{a: Flag, b: Flag}

def f(v: V, p: P2) -> Flag:
  match p:
    case P2{_, On{}}: Off{}

def main() -> Flag:
  On{}
