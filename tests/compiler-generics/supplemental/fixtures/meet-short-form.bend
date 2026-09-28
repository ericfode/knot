# The short form supplies both leading quantities; nested compact applications remain explicit.
type Flag is Data:
  Off{}
  On{}

type Error is Data:
  Stop{}

type Seq<a, -A: Kind(a)> is Kind(a):
  End{}
  Link{head: A, tail: Seq<a,A>}

type Result<a, b, -E: Kind(a), -A: Kind(b)> is Kind(a <&> b):
  Fail{error: E}
  Done{value: A}

def head(ts: Seq<&2,Flag>) -> Flag:
  match ts:
    case End{}:
      Off{}
    case Link{h,t}:
      h

def read(r: Result<Error,Seq<&2,Flag>>) -> Flag:
  match r:
    case Fail{e}:
      Off{}
    case Done{ts}:
      head(ts)

def round(x: Flag) -> Flag:
  read(Done{Link{x,End{}}})

def fail() -> Flag:
  read(Fail{Stop{}})

def main() -> Flag:
  round(On{})
