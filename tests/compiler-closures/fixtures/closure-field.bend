# Closures stored in a constructor field of a Type datatype, then unpacked and applied.
type Flag is Data:
  Off{}
  On{}

type Fn is Type:
  Fn{run: Flag -> Flag}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def xor(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: b
    case On{}: invert(b)

def call(f: Fn, x: Flag) -> Flag:
  match f:
    case Fn{g}: g(x)

def make(k: Flag) -> Fn:
  Fn{y => xor(k, y)}

def captured(k: Flag, x: Flag) -> Flag:
  call(make(k), x)

def named(x: Flag) -> Flag:
  call(Fn{invert}, x)

def main() -> Flag:
  captured(On{}, Off{})
