type Flag is Data:
  Off{}
  On{}

def f(x: (Flag < Flag : Nat)) -> Flag:
  On{}
