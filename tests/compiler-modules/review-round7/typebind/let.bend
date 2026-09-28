type Light is Type:
  Dark{}
  Lit{}

def f(x: Light) -> Light:
  Light = x
  y : Light = Lit{}
  y

def main() -> Light:
  f(Dark{})
