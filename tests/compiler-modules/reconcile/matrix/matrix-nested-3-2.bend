import ./lib/tree.bend as M

type Light is Type:
  Dark{}
  Lit{}

def f(x: M.Tree) -> Light:
  match x:
    case M.Branch{M.Stop{}, M.Leaf{M.Off{}}}: Lit{}
    case M.Branch{M.Stop{}, M.Leaf{M.Off{}}}: Dark{}
    case _: Dark{}

def main() -> Light:
  f(M.Branch{M.Stop{}, M.Leaf{M.Off{}}})
