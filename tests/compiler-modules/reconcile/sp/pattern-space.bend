type Light is Type:
  Dark{}
  Lit{}

def f(x: Light) -> Light:
  match x:
    case Dark {}: Lit{}
    case Lit{}: Dark{}

def main() -> Light:
  Lit{}
