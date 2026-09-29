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

def f(p: Opt, b: Flag) -> Flag:
  match p b:
    case Some{v} _:
    match v:
      case _: On{}
    case _ _: Off{}

def main() -> Flag:
  f(Some{On{}}, On{})
