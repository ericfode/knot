type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Opt is Data:
  None{}
  Some{v: Flag}

type Tp is Type:
  Tp{x: Flag}

type Pr is Type:
  Pr{l: Flag, r: Flag}

def h(a: Flag) -> Flag:
  a

def f(p: Opt) -> Flag:
  match p:
    case _: Off{}
    case Some{v}:
      match v:
        case Nope{}: On{}
        case _: Off{}
    case None{}: Off{}

def main() -> Flag:
  f(Some{On{}})
