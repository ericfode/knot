import Base

type Error is Data:
  Invalid{code: String}
  Exhausted{depth: U32}

type Quantity is Data:
  Erased{}
  Reusable{}
  Beyond{}

type Depth is Data:
  Shallow{}
  AtLimit{}
  Deep{}

type Outcome is Data:
  Accepted{}
  BadQuantity{}
  TooDeep{}
  WrongSum{}

def code(q: Quantity) -> U32:
  match q:
    case Erased{}: 0
    case Reusable{}: 2
    case Beyond{}: 3

def depth(d: Depth) -> U32:
  match d:
    case Shallow{}: 512
    case AtLimit{}: 4096
    case Deep{}: 4097

# syntax.choose and syntax.bind, verbatim: Result<Error, A> in short form.
def choose(-A: Type, condition: Bool, yes: Unit -> A, no: Unit -> A) -> A:
  match condition:
    case True{}: yes(Unit{})
    case False{}: no(Unit{})

def bind(-A: Data, -B: Data, result: Result<Error, A>, next: A -> Result<Error, B>) -> Result<Error, B>:
  match result:
    case Fail{e}: Fail{e}
    case Done{x}: next(x)

def quantity(+q: U32) -> Result<Error, U32>:
  choose(Result<Error, U32>, U32.is_gt(q, 2), u => Fail{Invalid{"quantity-range"}}, u => Done{q})

def bounded(+d: U32, +limit: U32) -> Result<Error, U32>:
  choose(Result<Error, U32>, U32.is_le(d, limit), u => Done{d}, u => Fail{Exhausted{d}})

def total(q: U32, d: U32) -> Result<Error, U32>:
  bind(U32, U32, quantity(q), x => bind(U32, U32, bounded(d, 4096), y => Done{U32.add(x, y)}))

def summed(ok: Bool) -> Outcome:
  match ok:
    case False{}: WrongSum{}
    case True{}: Accepted{}

def outcome(+expected: U32, r: Result<Error, U32>) -> Outcome:
  match r:
    case Fail{Invalid{c}}: BadQuantity{}
    case Fail{Exhausted{d}}: TooDeep{}
    case Done{n}: summed(U32.is_eq(n, expected))

def validate(q: Quantity, d: Depth) -> Outcome:
  +c = code(q)
  +n = depth(d)
  outcome(U32.add(c, n), total(c, n))

def main() -> Outcome:
  validate(Reusable{}, AtLimit{})
