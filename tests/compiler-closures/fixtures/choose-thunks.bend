# Unit thunks pick a branch, as S.choose does; each thunk captures only what its branch needs.
type Flag is Data:
  Off{}
  On{}

type Unit is Data:
  Unit{}

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

def choose(c: Flag, yes: Unit -> Flag, no: Unit -> Flag) -> Flag:
  match c:
    case On{}: yes(Unit{})
    case Off{}: no(Unit{})

def split(c: Flag, a: Flag, b: Flag) -> Flag:
  choose(c, u => a, u => b)

def shared(c: Flag, +a: Flag) -> Flag:
  choose(c, u => a, u => choose(a, v => Off{}, v => a))

def staged(c: Flag, a: Flag, b: Flag) -> Flag:
  choose(c, u => On{}, u =>
    +m = invert(a)
    both(m, xor(m, b)))

def main() -> Flag:
  split(On{}, Off{}, On{})
