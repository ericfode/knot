import Base

type Box<q, -A: Kind(q)> is Kind(q):
  Box{item: A}

def apply(f: U32 -> U32, x: U32) -> U32:
  f(x)

def capture(+x: U32) -> U32:
  apply(y => U32.add(x,y),1)

def descend(n: Nat) -> Nat:
  match n:
    case 0n: 0n
    case 1n+p: descend(p)

def pattern(xs: List<&2,Nat>, flag: Bool) -> Nat:
  match xs flag:
    case Con{Succ{n},tail} True{}: n
    case _ _: 0n

def char() -> Char: 'x'
def text() -> String: "lambda => import Array"
def float() -> F32: 1.5
def list() -> List<&2,U32>: [1,2]

def specialize(~f: U32 -> U32, x: U32) -> U32: f(x)

law same:
  for x: U32
  {x == x : U32}

def same(x): {==}
