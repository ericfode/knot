import ./lib/tree.bend as M

type Light is Type:
  Dark{}
  Lit{}

def f(x: M.Tree) -> Light:
  match x:
    case M.Branch{M.Leaf{M.On{}}, M.Stop{}}: Dark{}
    case _: Lit{}

def main() -> Light:
  f(M.Stop{})
