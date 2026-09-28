import Base

type Problem is Data:
  ExpectedU32{}
  OutOfRange{}

type Argument is Data:
  Moderate{}
  PastCap{}
  Blank{}
  Suffixed{}
  Padded{}
  Overflow{}

type Cap is Data:
  Wide{}
  Narrow{}

type Budget is Data:
  Missing{}
  Excess{}
  Fits512{}
  Fits7{}
  FitsOther{}

def argument(a: Argument) -> String:
  match a:
    case Moderate{}: "512"
    case PastCap{}: "4097"
    case Blank{}: ""
    case Suffixed{}: "4x"
    case Padded{}: "007"
    case Overflow{}: "4294967296"

def cap(c: Cap) -> U32:
  match c:
    case Wide{}: 4096
    case Narrow{}: 512

def within(fits: Bool, +x: U32) -> Result<Problem, Nat>:
  match fits:
    case True{}: Done{U32.to_nat(x)}
    case False{}: Fail{OutOfRange{}}

# driver.natural: U32.read, then U32.is_le against the cap, then U32.to_nat.
def natural(value: Maybe<&2, U32>, +cap: U32) -> Result<Problem, Nat>:
  match value:
    case None{}: Fail{ExpectedU32{}}
    case Some{+x}: within(U32.is_le(x, cap), x)

def fitted(+n: Nat) -> Budget:
  Bool.pick(Budget, Nat.is_eq(n, 512n), Fits512{},
    Bool.pick(Budget, Nat.is_eq(n, 7n), Fits7{}, FitsOther{}))

def budget_of(r: Result<Problem, Nat>) -> Budget:
  match r:
    case Fail{ExpectedU32{}}: Missing{}
    case Fail{OutOfRange{}}: Excess{}
    case Done{n}: fitted(n)

def budget(a: Argument, c: Cap) -> Budget:
  budget_of(natural(U32.read(argument(a)), cap(c)))

def main() -> Budget:
  budget(Padded{}, Narrow{})
