# A closure stays affine when every capture is Data: g is applied twice.
type Flag is Data:
  Off{}
  On{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: Off{}
    case On{}: b

def gate(+k: Flag) -> Flag -> Flag:
  x => both(k, x)

def bound(+k: Flag, x: Flag) -> Flag:
  g = gate(k)
  g(g(x))

def main() -> Flag:
  bound(On{}, On{})
