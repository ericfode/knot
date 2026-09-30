type Flag is Data:
  Off{}
  On{}

type V is Type:

type P2 is Type:
  P2{a: Flag, b: Flag}

type W is Data:

def f(x: W, y: Flag) -> Flag:
  match y:
    case On{}: Off{}

def main() -> Flag:
  On{}
