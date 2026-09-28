type Flag is Data:
  Off{}
  On{}

type Two<a, b> is Kind(a <&> b):
  T0{}
  T1{}

def read(x: Two) -> Flag:
  match x:
    case T0{}:
      Off{}
    case T1{}:
      On{}

def main() -> Flag:
  read(T1{})
