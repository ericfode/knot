type Light is Type:
  Dark{}
  Lit{}

def f(a.b: Light, x: Light, y: Light) -> Light:
  match x y:
    case a.b Lit{}: a.b
    case _ _: Dark{}

def main() -> Light:
  f(Dark{}, Lit{}, Lit{})
