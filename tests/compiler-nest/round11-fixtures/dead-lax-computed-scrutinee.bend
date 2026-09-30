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
    case _: Off{}
    case On{}:
      match h(a):
        case _: On{}

def main() -> Flag:
  f(On{})
