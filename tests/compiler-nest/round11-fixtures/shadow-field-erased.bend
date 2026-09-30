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

type Q is Type:
  Q{-Flag: Flag, y: Flag}

def f(a: Flag) -> Flag:
  a

def main() -> Flag:
  f(On{})
