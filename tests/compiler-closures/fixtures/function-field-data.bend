# A function-typed field in a Data datatype: a function field never sits in Data.
type Flag is Data:
  Off{}
  On{}

type Fn is Data:
  Fn{run: Flag -> Flag}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def call(f: Fn, x: Flag) -> Flag:
  match f:
    case Fn{g}: g(x)

def main() -> Flag:
  call(Fn{invert}, On{})
