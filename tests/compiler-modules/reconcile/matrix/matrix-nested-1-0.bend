import ./lib/tree.bend as M

type Light is Type:
  Dark{}
  Lit{}

def f(x: M.Tree) -> Light:
  match x:
    case M.Leaf{M.Off{}}: Lit{}
    case _: Dark{}

def main() -> Light:
  f(M.Leaf{M.Off{}})
