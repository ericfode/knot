type Flag is Data:
  Off{}
  On{}

type V is Type:

def f(x: Flag, v: V) -> Flag:
  match x v:
    case On{} _: Off{}

def main() -> Flag:
  On{}
