type Flag is Data:
  Off{}
  On{}

type V is Type:

def f(y: Flag, x: V) -> Flag:
  match y x:
    case On{} _: Off{}

def main() -> Flag:
  On{}
