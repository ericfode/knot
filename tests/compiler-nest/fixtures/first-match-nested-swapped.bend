# The rows of first-match-nested with the first two swapped: a = d = On{} now reaches R2.
type Flag is Data:
  Off{}
  On{}

type Pair is Type:
  Pair{l: Flag, r: Flag}

type Quad is Type:
  Quad{a: Pair, b: Pair}

type Deep is Type:
  Deep{q: Quad}

type Row is Data:
  R1{}
  R2{}
  R3{}
  R4{}

def rank(d: Deep) -> Row:
  match d:
    case Deep{Quad{_, Pair{_, On{}}}}: R2{}
    case Deep{Quad{Pair{On{}, _}, _}}: R1{}
    case Deep{Quad{Pair{_, On{}}, Pair{Off{}, _}}}: R3{}
    case Deep{_}: R4{}

def probe(a: Flag, b: Flag, c: Flag, d: Flag) -> Row:
  rank(Deep{Quad{Pair{a, b}, Pair{c, d}}})

def main() -> Row:
  probe(On{}, Off{}, Off{}, On{})
