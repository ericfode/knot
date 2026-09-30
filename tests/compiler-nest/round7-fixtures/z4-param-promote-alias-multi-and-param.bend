type Flag is Data:
  Off{}
  On{}

type Box is Data:
  B{f: Flag}
  E{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def f(a: Flag, b: Flag) -> Flag:
  match a b:
    case +y On{}: both(y, both(a, a))
    case _ Off{}: Off{}
