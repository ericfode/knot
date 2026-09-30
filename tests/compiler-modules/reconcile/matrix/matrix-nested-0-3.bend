import ./lib/tree.bend as M

type Light is Type:
  Dark{}
  Lit{}

def f(x: M.Tree) -> Light:
  match x:
    case all: Lit{}
    case M.Leaf{M.On{}}: Dark{}

def main() -> Light:
  f(M.Leaf{M.On{}})
