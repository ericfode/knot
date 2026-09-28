# Affine closures may be dropped: built and never applied, or applied in one arm only; arms take the maximum use.
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

def unused(x: Flag, k: Flag) -> Flag:
  f : Flag -> Flag = y => xor(k, y)
  x

def one_arm(x: Flag, f: Flag -> Flag) -> Flag:
  match x:
    case On{}: f(Off{})
    case Off{}: On{}

def both_arms(x: Flag, f: Flag -> Flag) -> Flag:
  match x:
    case On{}: f(Off{})
    case Off{}: f(On{})

def run_one(x: Flag, k: Flag) -> Flag:
  one_arm(x, y => xor(k, y))

def run_both(x: Flag, k: Flag) -> Flag:
  both_arms(x, y => xor(k, y))

def main() -> Flag:
  unused(On{}, Off{})
