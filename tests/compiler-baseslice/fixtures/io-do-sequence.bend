import Base

# A stand-in for File: closing it is a pure step here.
type Handle is Data:
  Handle{id: U32}

type Case is Data:
  Missing{}
  Loaded{}
  Blank{}

type Outcome is Data:
  Source{}
  NoSource{}
  HostRead{}
  HaltedOther{}

def emit(-A: Type, x: A) -> IO(A):
  R => k => k(x)

def close(h: Handle) -> IO(Unit):
  emit(Unit, Unit{})

def outcome(op: IO.OP<Outcome>) -> Outcome:
  match op:
    case Emit{v}: v
    case Halt{+code, message}:
      Bool.pick(Outcome, Bool.and(U32.is_eq(code, 5),
        String.eq(message, "HostFailure\tread\t2\tNo such file")), HostRead{}, HaltedOther{})

def run(m: IO(Outcome)) -> Outcome:
  outcome(m(Outcome, x => Emit{x}))

def read(c: Case) -> Handle & Result<&1, &1, U32 & String, String>:
  match c:
    case Missing{}: (Handle{3}, Fail{(2, "No such file")})
    case Loaded{}: (Handle{3}, Done{"type"})
    case Blank{}: (Handle{3}, Done{""})

def read_result(result: Result<&1, &1, U32 & String, String>) -> IO(Outcome):
  match result:
    case Fail{(code, message)}:
      IO.die(Outcome, 5, String.concat(["HostFailure\tread\t", U32.show(code), "\t", message]))
    case Done{+text}: emit(Outcome, Bool.pick(Outcome, String.eq(text, ""), NoSource{}, Source{}))

# driver.read_pair: destructure, close in a do block, then continue.
def read_pair(pair: Handle & Result<&1, &1, U32 & String, String>) -> IO(Outcome):
  (handle, result) = pair
  do IO<Outcome>:
    close(handle)
    read_result(result)

def load(c: Case) -> Outcome:
  run(read_pair(read(c)))

def main() -> Outcome:
  load(Missing{})
