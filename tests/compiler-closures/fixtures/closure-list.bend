# A list of closures in a Type datatype; each closure is applied exactly once as the list is consumed.
type Flag is Data:
  Off{}
  On{}

type Fns is Type:
  Stop{}
  Then{f: Flag -> Flag, rest: Fns}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def xor(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: b
    case On{}: invert(b)

def run_all(fs: Fns, x: Flag) -> Flag:
  match fs:
    case Stop{}: x
    case Then{f, rest}: run_all(rest, f(x))

def pipeline(k: Flag) -> Fns:
  Then{invert, Then{y => xor(k, y), Then{y => y, Stop{}}}}

def run(k: Flag, x: Flag) -> Flag:
  run_all(pipeline(k), x)

def main() -> Flag:
  run(On{}, Off{})
