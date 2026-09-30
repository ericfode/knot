import ./lib/types.bend as T

type Light is Type:
  Dark{}
  Lit{}

def f(x: T.Rune()) -> Light:
  match x, x:
    case 'a', _: Lit{}
    case _, _: Dark{}

def main() -> Light:
  f('a')
