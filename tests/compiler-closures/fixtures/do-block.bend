# do-notation over a fixture monad desugars into bind calls with continuation lambdas (do is S3).
type Flag is Data:
  Off{}
  On{}

type Opt is Data:
  None{}
  Some{value: Flag}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def Opt.pure(x: Flag) -> Opt:
  Some{x}

def Opt.bind(-A: Type, m: Opt, next: Flag -> Opt) -> Opt:
  match m:
    case None{}: None{}
    case Some{x}: next(x)

def need(x: Flag) -> Opt:
  match x:
    case Off{}: None{}
    case On{}: Some{On{}}

def unwrap(m: Opt) -> Flag:
  match m:
    case None{}: Off{}
    case Some{x}: invert(x)

def run(a: Flag, b: Flag) -> Flag:
  unwrap(do Opt<>:
    x : Flag <- need(a)
    y : Flag <- need(b)
    return invert(y))

def main() -> Flag:
  run(On{}, On{})
