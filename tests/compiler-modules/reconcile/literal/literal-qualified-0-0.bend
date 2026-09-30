import ./lib/types.bend as T

type Light is Type:
  Dark{}
  Lit{}

def f(x: T.Word()) -> Light:
  match x:
    case 0: Lit{}
    case _: Dark{}

def main() -> Light:
  f(0)
