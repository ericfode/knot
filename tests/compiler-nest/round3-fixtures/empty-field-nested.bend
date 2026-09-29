type Flag is Data:
  Off{}
  On{}

type V is Type:

type P is Type:
  P{v: V, a: Flag}

def f(p: P) -> Flag:
  match p:
    case P{_, On{}}: Off{}

def main() -> Flag:
  On{}
