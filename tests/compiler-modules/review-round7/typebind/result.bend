type Light is Type:
  Dark{}
  Lit{}

def f(Light: Light) -> Light:
  Lit{}

def main() -> Light:
  f(Dark{})
