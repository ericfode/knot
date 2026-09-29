type Flag is Data:
  Off{}
  On{}

type Box is Data:
  B{f: Flag}
  E{}

type TBox is Type:
  TB{f: Flag}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def f(x: TBox) -> Flag:
  match x:
    case TB{g}:
      match g:
        case +y: both(y, y)
