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

def f(a: Flag) -> Flag:
  match a:
    case On{}: Off{}
    case On{}:
      match a:
        case On: On{}
        case _: Off{}
    case Off{}: On{}

def main() -> Flag:
  f(On{})
