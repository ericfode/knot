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

type Nat is Data:
  Zero{}
  Succ{pred: Nat}

def f(b: Flag, n: Nat) -> Flag:
  match b n:
    case _   10n: On{}
    case _ _: Off{}

def probe(a: Flag, k: Flag) -> Flag:
  match k:
    case Off{}: f(a, Zero{})
    case On{}: f(a, Succ{Zero{}})

def main() -> Flag:
  probe(On{}, Off{})
