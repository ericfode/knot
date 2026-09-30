# 2 rows, depth-3 nested pattern over a 14-constructor type.
type Flag is Data:
  Off{}
  On{}

type T is Type:
  K0{}
  K1{}
  K2{}
  K3{}
  K4{}
  K5{}
  K6{}
  K7{}
  K8{}
  K9{}
  K10{}
  K11{}
  K12{}
  W{t: T}

def f(x: T) -> Flag:
  match x:
    case W{W{W{K0{}}}}: On{}
    case _: Off{}

def main() -> Flag:
  f(W{W{W{K0{}}}})
