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

def f(n: Nat, b: Flag) -> Flag:
  match n b:
    case 0n _: On{}
    case _ _: Off{}

def probe(a: Flag, k: Flag) -> Flag:
  match k:
    case Off{}: f(Zero{}, a)
    case On{}: f(Succ{Zero{}}, a)

def main() -> Flag:
  probe(On{}, Off{})
