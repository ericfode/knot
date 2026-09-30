type Flag is Data:
  Off{}
  On{}

type P is Type:
  P{a: Flag, b: Flag}

def f(p: P, z: Flag) -> Flag:
  match p z:
    case P{x, On # c
      {}} v: v
    case _ _: Off{}

def main() -> Flag:
  f(P{On{}, On{}}, Off{})
