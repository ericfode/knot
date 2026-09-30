import ./lib/types.bend as T

type Light is Type:
  Dark{}
  Lit{}

def f(x: T.Count()) -> Light:
  match x:
    case 0n: Lit{}
    case _: Dark{}

def main() -> Light:
  f(0n)
