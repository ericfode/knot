# Nested lambdas read outer binders and outer captures; a lambda binder shadows by nesting.
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

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: Off{}
    case On{}: b

def either(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: b
    case On{}: On{}

def majority(a: Flag, b: Flag, c: Flag) -> Flag:
  match a:
    case Off{}: both(b, c)
    case On{}: either(b, c)

def apply(f: Flag -> Flag, x: Flag) -> Flag:
  f(x)

def deep(a: Flag, b: Flag, c: Flag, d: Flag) -> Flag:
  m : Flag = invert(a)
  h : Flag -> Flag -> Flag -> Flag = x => y => z => majority(m, xor(x, y), z)
  h(b)(c)(d)

def shadow(x: Flag) -> Flag:
  apply(x => invert(x), x)

def inner(a: Flag, b: Flag) -> Flag:
  g : Flag -> Flag -> Flag = x => x => x
  g(a, b)

def main() -> Flag:
  deep(On{}, On{}, Off{}, On{})
