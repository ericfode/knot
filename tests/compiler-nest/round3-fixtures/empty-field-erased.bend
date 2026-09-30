type Flag is Data:
  Off{}
  On{}

type V is Type:

type Q is Type:
  Q{-v: V, a: Flag}

def f(p: Q) -> Flag:
  match p:
    case Q{v, On{}}: Off{}

def main() -> Flag:
  On{}
