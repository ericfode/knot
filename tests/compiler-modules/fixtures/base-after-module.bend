import ./lib/own-bool.bend as M
import Base

type Light is Type:
  Dark{}
  Lit{}

def see(x: M.Bool, y: Bool) -> Light:
  match x:
    case M.No{}: Dark{}
    case M.Yes{}:
      match y:
        case False{}: Dark{}
        case True{}: Lit{}

def main() -> Light:
  see(M.Yes{}, True{})
