# A closure-returning definition over-applied, and a curried closure variable under-applied.
type Flag is Data:
  Off{}
  On{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: Off{}
    case On{}: b

def gate(k: Flag) -> Flag -> Flag:
  x => both(k, x)

def over(k: Flag, x: Flag) -> Flag:
  gate(k, x)

def first_of(x: Flag, next: Flag -> Flag -> Flag) -> Flag -> Flag:
  next(x)

def under(a: Flag, b: Flag) -> Flag:
  first_of(a, x => y => both(y, x))(b)

def main() -> Flag:
  over(On{}, Off{})
