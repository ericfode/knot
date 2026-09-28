import Base

type Light is Type:
  Dark{}
  Lit{}

def see(x: Bool) -> Light:
  match x:
    case False{}: Dark{}
    case True{}: Lit{}

def f(x: Light) -> Light:
  T = Bool
  y : T = True{}
  see(y)

def main() -> Light:
  f(Lit{})
