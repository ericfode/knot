type V is Type:

type Flag is Data:
  Off{}
  On{}

def f(v: V) -> Flag:
  match v:
    case +y: On{}
