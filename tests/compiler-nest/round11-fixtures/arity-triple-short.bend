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

def f(a: Flag, b: Flag, c: Flag) -> Flag:
  match a b c:
    case _ _ _: On{}
    case On{} _: Off{}

def main() -> Flag:
  f(On{}, On{}, On{})
