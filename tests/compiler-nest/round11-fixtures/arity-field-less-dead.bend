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

type Bx is Type:
  Bx{p: Pr}

def f(x: Bx) -> Flag:
  match x:
    case Bx{Pr{a, b}}: On{}
    case Bx{Pr{a}}: Off{}

def main() -> Flag:
  f(Bx{Pr{On{}, On{}}})
