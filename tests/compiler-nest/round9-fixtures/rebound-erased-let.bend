type Light is Type:
  Dark{}
  Lit{}

def f(a.b: Light, x: Light) -> Light:
  -a.b = x
  x

def main() -> Light:
  f(Dark{}, Lit{})
