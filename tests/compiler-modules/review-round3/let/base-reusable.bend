import ./lib/keep-reusable.bend as M
import Base

type Light is Type:
  Dark{}
  Lit{}

def see(x: Bool) -> Light:
  match x:
    case True{}: Dark{}
    case False{}: Lit{}

def main() -> Light:
  see(M.keep(False{}))
