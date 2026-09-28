import Base

type Flag is Data:
  Off{}
  On{}

type Two is Data:
  Two{left: Flag, right: Flag}

type Ghost is Data:
  Ghost{-proof: Flag}
  Real{}

def two(left: Flag, -proof: Flag, right: Flag) -> Two:
  Two{left,right}

def succ(n: Nat) -> Nat:
  Succ{n}

def size(s: String) -> Nat:
  String.length(s)

def code(c: Char) -> U32:
  Char.to_u32(c)

def is_zero(x: U32) -> Bool:
  U32.is_eq(x,0)

def real(g: Ghost) -> Flag:
  match g:
    case Ghost{p}: Off{}
    case Real{}: On{}

def text(f: Flag) -> String:
  "ab"

def main() -> Two:
  two(On{},Off{},Off{})
