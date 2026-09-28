import Base

type Digits is Data:
  Largest{}
  PastLargest{}
  WrapsToSmall{}
  Padded{}
  Blank{}
  BelowZero{}
  AboveNine{}
  Signed{}
  Leading{}
  Nought{}
  Nearly{}

type Read is Data:
  Absent{}
  ReadZero{}
  ReadSeven{}
  ReadMax{}
  ReadOther{}

def digits(d: Digits) -> String:
  match d:
    case Largest{}: "4294967295"
    case PastLargest{}: "4294967296"
    case WrapsToSmall{}: "4294967300"
    case Padded{}: "00000000004294967295"
    case Blank{}: ""
    case BelowZero{}: "1/"
    case AboveNine{}: ":"
    case Signed{}: "-1"
    case Leading{}: "007"
    case Nought{}: "0"
    case Nearly{}: "429496729"

def value(+x: U32) -> Read:
  Bool.pick(Read, U32.is_eq(x, 0), ReadZero{},
  Bool.pick(Read, U32.is_eq(x, 7), ReadSeven{},
  Bool.pick(Read, U32.is_eq(x, 4294967295), ReadMax{}, ReadOther{})))

def seen(m: Maybe<&2, U32>) -> Read:
  match m:
    case None{}: Absent{}
    case Some{x}: value(x)

def read(d: Digits) -> Read:
  seen(U32.read(digits(d)))

def main() -> Read:
  read(Padded{})
