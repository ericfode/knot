# A wildcard after a single-constructor row names an unbound variable.
type Flag is Data:
  Off{}
  On{}

type Box is Type:
  Box{f: Flag}

def f(b: Box) -> Flag:
  match b:
    case Box{v}: v
    case _: nope

def probe(a: Flag) -> Flag:
  f(Box{a})

def main() -> Flag:
  probe(On{})
