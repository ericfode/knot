type Light is Type:
  Dark{}
  Lit{}

def f(a.b: Light, x: Light) -> Light:
  match x:
    case a.b: a.b

def main() -> Light:
  f(Dark{}, Lit{})
