type Light is Type:
  Dark{}
  Lit{}

type Flag is Type:
  Off{}
  On{}

def f(Light: Flag) -> Light:
  Lit{}

def main() -> Light:
  f(On{})
