# Two thunks capture the same affine value; building both consumes it twice, although only one runs.
type Flag is Data:
  Off{}
  On{}

type Unit is Data:
  Unit{}

def choose(c: Flag, yes: Unit -> Flag, no: Unit -> Flag) -> Flag:
  match c:
    case On{}: yes(Unit{})
    case Off{}: no(Unit{})

def shared(c: Flag, a: Flag) -> Flag:
  choose(c, u => a, u => a)

def main() -> Flag:
  shared(On{}, Off{})
