import ./lib/types.bend as T

type Light is Type:
  Dark{}
  Lit{}

def f(x: T.Rune()) -> Light:
  match x:
    case 'a': Lit{}
    case _: Dark{}

def main() -> Light:
  f('a')
