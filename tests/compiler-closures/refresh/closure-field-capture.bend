type Flag is Data:
  Off{}
  On{}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def xor(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: b
    case On{}: invert(b)

def keep(a: Flag, b: Flag) -> Flag:
  a

def apply(f: Flag -> Flag, x: Flag) -> Flag:
  f(x)

type Box is Type:
  Box{run: Flag -> Flag}

def close(box: Box) -> Flag -> Flag:
  match box:
    case Box{f}: x => f(x)

def main() -> Flag:
  close(Box{invert})(Off{})
