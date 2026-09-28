# A match arm promotes a field binder with +, and every S.choose thunk may capture it, as src/lex.bend does.
type Flag is Data:
  Off{}
  On{}

type Unit is Data:
  Unit{}

type Pair is Data:
  Pair{a: Flag, b: Flag}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def xor(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: b
    case On{}: invert(b)

def choose(c: Flag, yes: Unit -> Flag, no: Unit -> Flag) -> Flag:
  match c:
    case On{}: yes(Unit{})
    case Off{}: no(Unit{})

def promoted(c: Flag, p: Pair) -> Flag:
  match p:
    case Pair{+a, b}: choose(c, u => a, u => choose(a, v => xor(a, b), v => a))

def run(c: Flag, a: Flag, b: Flag) -> Flag:
  promoted(c, Pair{a, b})

def main() -> Flag:
  run(Off{}, On{}, Off{})
