import Base

type Node is Data:
  Leaf{name: String}

type Param is Data:
  Param{name: String, quantity: U32}

type Count is Data:
  Nought{}
  One{}
  Two{}

type Verdict is Data:
  Mismatch{}
  Matches{}

type Order is Data:
  Fewer{}
  Same{}
  More{}

def args(c: Count) -> List<&2, Node>:
  match c:
    case Nought{}: []
    case One{}: [Leaf{"x"}]
    case Two{}: [Leaf{"x"}, Leaf{"y"}]

def params(c: Count) -> List<&2, Param>:
  match c:
    case Nought{}: []
    case One{}: [Param{"a", 1}]
    case Two{}: [Param{"a", 1}, Param{"b", 2}]

def verdict(b: Bool) -> Verdict:
  match b:
    case False{}: Mismatch{}
    case True{}: Matches{}

def order(c: Cmp) -> Order:
  match c:
    case LT{}: Fewer{}
    case EQ{}: Same{}
    case GT{}: More{}

# check.bend: two lists of different element types compared by length.
def arity(a: Count, p: Count) -> Verdict:
  verdict(Nat.is_eq(List.length(Node, args(a)), List.length(&2, Param, params(p))))

def compare(a: Count, p: Count) -> Order:
  order(Nat.cmp(List.length(&2, Node, args(a)), List.length(&2, Param, params(p))))

def main() -> Verdict:
  arity(Two{}, Two{})
