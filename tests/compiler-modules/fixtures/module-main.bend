import ./lib/with-main.bend as W

type Light is Type:
  Dark{}
  Lit{}

def see(x: W.Mark) -> Light:
  match x:
    case W.Stamp{}: Lit{}

def main() -> Light:
  see(W.main())
