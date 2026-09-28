type Light is Type:
  Dark{}
  Lit{}

def f(x: Light) -> Light:
  match x:
    case a.b: a.b

def main() -> Light:
  f(Lit{})
