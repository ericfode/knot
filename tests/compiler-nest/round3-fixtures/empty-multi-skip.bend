type Flag is Data:
  Off{}
  On{}

type V is Type:

def f(x: Flag, v: V, y: Flag) -> Flag:
  match v y:
    case _ On{}: Off{}

def main() -> Flag:
  On{}
