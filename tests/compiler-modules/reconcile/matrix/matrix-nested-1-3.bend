import ./lib/tree.bend as M

type Light is Type:
  Dark{}
  Lit{}

def f(x: M.Tree) -> Light:
  match x:
    case all: Lit{}
    case M.Leaf{M.Off{}}: Dark{}

def main() -> Light:
  f(M.Leaf{M.Off{}})
