# Nested patterns over fields with several constructors; overlapping rows resolve in order.
type Flag is Data:
  Off{}
  On{}

type Sel is Data:
  No{}
  SomeOff{}
  SomeOn{}

type Opt is Type:
  None{}
  Some{v: Flag}

type Two is Type:
  Two{a: Opt, b: Opt}

type Row is Data:
  R1{}
  R2{}
  R3{}
  R4{}
  R5{}

def tag(v: Flag) -> Row:
  match v:
    case Off{}: R2{}
    case On{}: R3{}

def pick(t: Two) -> Row:
  match t:
    case Two{Some{On{}}, _}: R1{}
    case Two{_, Some{v}}: tag(v)
    case Two{None{}, None{}}: R4{}
    case Two{Some{Off{}}, None{}}: R5{}

def opt(s: Sel) -> Opt:
  match s:
    case No{}: None{}
    case SomeOff{}: Some{Off{}}
    case SomeOn{}: Some{On{}}

def probe(a: Sel, b: Sel) -> Row:
  pick(Two{opt(a), opt(b)})

def main() -> Row:
  probe(SomeOff{}, SomeOn{})
