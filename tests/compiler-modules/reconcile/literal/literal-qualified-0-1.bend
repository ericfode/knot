import ./lib/types.bend as T

type Light is Type:
  Dark{}
  Lit{}

def f(x: T.Word()) -> Light:
  match x, x:
    case 0, _: Lit{}
    case _, _: Dark{}

def main() -> Light:
  f(0)
