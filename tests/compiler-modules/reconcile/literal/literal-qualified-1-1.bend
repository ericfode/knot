import ./lib/types.bend as T

type Light is Type:
  Dark{}
  Lit{}

def f(x: T.Count()) -> Light:
  match x, x:
    case 0n, _: Lit{}
    case _, _: Dark{}

def main() -> Light:
  f(0n)
