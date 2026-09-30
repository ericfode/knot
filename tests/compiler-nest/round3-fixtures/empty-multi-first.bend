type Flag is Data:
  Off{}
  On{}

type V is Type:

def f(v: V, x: Flag, y: Flag) -> Flag:
  match v x y:
    case _ On{} _: Off{}

def main() -> Flag:
  On{}
