# Result steps chained in continuation style, as S.bind does; a later lambda reads an earlier result.
type Flag is Data:
  Off{}
  On{}

type Outcome is Data:
  Failed{}
  Low{}
  High{}

type Res is Data:
  Fail{}
  Done{value: Flag}

def xor(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: b
    case On{}:
      match b:
        case Off{}: On{}
        case On{}: Off{}

def guard(x: Flag, y: Flag) -> Res:
  match x:
    case Off{}: Fail{}
    case On{}: Done{y}

def bind(r: Res, next: Flag -> Res) -> Res:
  match r:
    case Fail{}: Fail{}
    case Done{x}: next(x)

def level(x: Flag) -> Outcome:
  match x:
    case Off{}: Low{}
    case On{}: High{}

def report(r: Res) -> Outcome:
  match r:
    case Fail{}: Failed{}
    case Done{x}: level(x)

def chain(a: Flag, b: Flag, c: Flag) -> Outcome:
  report(bind(guard(a, b), +x => bind(guard(x, c), y => Done{xor(x, y)})))

def main() -> Outcome:
  chain(On{}, On{}, Off{})
