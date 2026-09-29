import ./lib/with-base.bend as W

type Light is Type:
  Dark{}
  Lit{}

def see(x: Bool) -> Light:
  match x:
    case False{}: Dark{}
    case True{}: Lit{}

def main() -> Light:
  see(Bool.not(W.yes()))
