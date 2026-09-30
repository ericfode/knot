type Flag is Data:
  Off{}
  On{}

type V is Type:

type P is Type:
  P{a: Flag, v: V}

def f(p: P) -> Flag:
  match p:
    case P{a, v}:
      match a:
        case On{}: Off{}

def main() -> Flag:
  On{}
