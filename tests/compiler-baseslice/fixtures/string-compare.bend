import Base

# Equal prefixes with different tails, a proper prefix each way, and "".
type Text is Data:
  Blank{}
  Ab{}
  Abc{}
  Ac{}
  Bee{}

type Verdict is Data:
  Differ{}
  Alike{}

type Order is Data:
  Before{}
  Same{}
  After{}
  Broken{}

def text(t: Text) -> String:
  match t:
    case Blank{}: ""
    case Ab{}: "ab"
    case Abc{}: "abc"
    case Ac{}: "ac"
    case Bee{}: "b"

def verdict(b: Bool) -> Verdict:
  match b:
    case False{}: Differ{}
    case True{}: Alike{}

def order(c: Cmp) -> Order:
  match c:
    case LT{}: Before{}
    case EQ{}: Same{}
    case GT{}: After{}

def intact(ok: Bool, o: Order) -> Order:
  match ok:
    case False{}: Broken{}
    case True{}: o

# String.cmp returns both Strings with the order; they must be the inputs.
def settle(+a: String, +b: String, r: (String & String) & Cmp) -> Order:
  ((a2, b2), c) = r
  intact(Bool.and(String.eq(a, a2), String.eq(b, b2)), order(c))

def equal(l: Text, r: Text) -> Verdict:
  verdict(String.eq(text(l), text(r)))

def compare(l: Text, r: Text) -> Order:
  +a = text(l)
  +b = text(r)
  settle(a, b, String.cmp(a, b))

def main() -> Order:
  compare(Abc{}, Ac{})
