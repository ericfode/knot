import ./lib/tree.bend as M

type Light is Type:
  Dark{}
  Lit{}

def f(x: M.Tree, y: M.Flag) -> Light:
  match x, y:
    case M.Branch{M.Stop{}, M.Leaf{M.Off{}}}, M.On{}: Lit{}
    case _ _: Dark{}

def main() -> Light:
  f(M.Branch{M.Stop{}, M.Leaf{M.Off{}}}, M.On{})
