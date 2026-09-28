import Base

# Quantity codes as catalog.bend spells them: 0 erased, 1 affine, 2 reusable.
type Quantity is Data:
  Erased{}
  Affine{}
  Reusable{}
  Beyond{}

type Flag is Data:
  Off{}
  On{}

type Verdict is Data:
  Refused{}
  Allowed{}
  OutOfRange{}

def code(q: Quantity) -> U32:
  match q:
    case Erased{}: 0
    case Affine{}: 1
    case Reusable{}: 2
    case Beyond{}: 3

def bool(f: Flag) -> Bool:
  match f:
    case Off{}: False{}
    case On{}: True{}

def allowed(b: Bool) -> Verdict:
  match b:
    case False{}: Refused{}
    case True{}: Allowed{}

# catalog.field_kind, verbatim.
def field_kind(+data: Bool, +q: U32, +child: Bool) -> Bool:
  Bool.and(Bool.or(U32.is_ne(q, 2), child),
    Bool.or(Bool.not(data), Bool.or(U32.is_eq(q, 0), child)))

def field(data: Flag, q: Quantity, child: Flag) -> Verdict:
  allowed(field_kind(bool(data), code(q), bool(child)))

# catalog.quantity: a code past 2 is out of range before the kind check.
def ranged(high: Bool, +q: U32, data: Bool) -> Verdict:
  match high:
    case True{}: OutOfRange{}
    case False{}: allowed(Bool.not(Bool.and(U32.is_eq(q, 2), Bool.not(data))))

def quantity(q: Quantity, data: Flag) -> Verdict:
  +c = code(q)
  ranged(U32.is_gt(c, 2), c, bool(data))

def main() -> Verdict:
  field(On{}, Reusable{}, Off{})
