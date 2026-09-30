type Flag is Data:
  Off{}
  On{}

def f(a: Flag, b: Flag) -> Flag:
  k = a
  match k:
    case +y: b
