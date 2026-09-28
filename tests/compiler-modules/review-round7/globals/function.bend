type Light is Type:
  Dark{}
  Lit{}

def flip(x: Light) -> Light:
  match x:
    case Dark{}: Lit{}
    case Lit{}: Dark{}

def f(x: Light) -> Light:
  -g = flip
  x

def main() -> Light:
  f(Lit{})
