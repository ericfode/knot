type Flag is Data:
  Off{}
  On{}

type V is Type:

def f(x: Flag, v: V, y: Flag) -> Flag:
  match x v y:
    case On{} _ On{}: Off{}
    case Off{} _ _: On{}

def main() -> Flag:
  On{}
