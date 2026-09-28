type Light is Type:
  Dark{}
  Lit{}

def flip(x: Light) -> Light:
  match x:
    case Dark{}: Lit{}
    case Lit{}: Dark{}

def g(flip: Light, b: Light) -> Light:
  flip(b)

def main() -> Light:
  g(Dark{}, Dark{})
