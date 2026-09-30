type Flag is Data:
  Off{}
  On{}

type Pair is Data:
  P{l: Flag, r: Flag}

def f(a: Flag) -> Flag:
  match a:
    case On{}: On{} case Off{}: Off{}
