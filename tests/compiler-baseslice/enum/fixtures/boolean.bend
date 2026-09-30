# Qualification book: the seven pinned Base declarations below are verbatim.
# This is source-body qualification; the import loader is gated separately.

type Unit is Data:
  Unit{}

type Bool is Data:
  False{}
  True{}

type Cmp is Data:
  LT{}
  EQ{}
  GT{}

def Bool.not(b: Bool) -> Bool:
  match b:
    case False{}:
      True{}
    case True{}:
      False{}

def Bool.and(a: Bool, b: Bool) -> Bool:
  match a:
    case False{}:
      False{}
    case True{}:
      b

def Bool.or(a: Bool, b: Bool) -> Bool:
  match a:
    case False{}:
      b
    case True{}:
      True{}

def Cmp.is_eq(c: Cmp) -> Bool:
  match c:
    case LT{}:
      False{}
    case EQ{}:
      True{}
    case GT{}:
      False{}

def neg(x: Bool) -> Bool:
  Bool.not(x)

def conjunction(a: Bool, b: Bool) -> Bool:
  Bool.and(a,b)

def disjunction(a: Bool, b: Bool) -> Bool:
  Bool.or(a,b)

def composed(a: Bool, b: Bool, c: Bool) -> Bool:
  Bool.and(Bool.or(a,b),Bool.not(c))

def reusable(+x: Bool) -> Bool:
  Bool.or(x,Bool.not(x))

def main() -> Bool:
  neg(False{})
