# Match arms return different closures; a lambda in an arm captures that arm's field.
type Flag is Data:
  Off{}
  On{}

type Wrap is Data:
  Plain{}
  Tagged{tag: Flag}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def xor(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: b
    case On{}: invert(b)

def pick(x: Flag) -> Flag -> Flag:
  match x:
    case On{}: y => y
    case Off{}: y => invert(y)

def tagged(w: Wrap) -> Flag -> Flag:
  match w:
    case Plain{}: y => invert(y)
    case Tagged{t}: y => xor(t, y)

def run(x: Flag, y: Flag) -> Flag:
  pick(x)(y)

def run_plain(y: Flag) -> Flag:
  tagged(Plain{})(y)

def run_tagged(t: Flag, y: Flag) -> Flag:
  tagged(Tagged{t})(y)

def main() -> Flag:
  run(Off{}, On{})
