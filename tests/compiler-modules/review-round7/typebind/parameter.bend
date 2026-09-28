type Light is Type:
  Dark{}
  Lit{}

type Flag is Type:
  Off{}
  On{}

def f(Light: Light, x: Light) -> Flag:
  On{}

def main() -> Flag:
  f(Dark{}, Lit{})
