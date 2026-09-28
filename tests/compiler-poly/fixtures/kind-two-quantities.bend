# Two-quantity Res<a,b,..> at Kind(a <&> b): explicit &1,&1 and &2,&2 and &2,&1, one generic reader, a + reuse.
type Flag is Data:
  Off{}
  On{}

type Fault is Data:
  Invalid{}
  Unsupported{}

type Res<a, b, -E: Kind(a), -A: Kind(b)> is Kind(a <&> b):
  Fail{error: E}
  Done{value: A}

def done(a, b, -E: Kind(a), -A: Kind(b), r: Res<a, b, E, A>) -> Flag:
  match r:
    case Fail{e}: Off{}
    case Done{x}: On{}

def both(x: Flag, y: Flag) -> Flag:
  match x:
    case Off{}: Off{}
    case On{}: y

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def make(f: Flag, g: Flag) -> Res<&2,&2,Fault,Flag>:
  match f:
    case Off{}: Fail{Invalid{}}
    case On{}: Done{g}

def value(r: Res<&2,&2,Fault,Flag>) -> Flag:
  match r:
    case Fail{e}: Off{}
    case Done{x}: x

def shared(f: Flag, g: Flag) -> Flag:
  +r = make(f,g)
  both(done(&2,&2,Fault,Flag,r),value(r))

def make_short(f: Flag) -> Res<Fault,Flag>:
  match f:
    case Off{}: Fail{Unsupported{}}
    case On{}: Done{On{}}

def read_long(r: Res<&1,&1,Fault,Flag>) -> Flag:
  done(&1,&1,Fault,Flag,r)

def affine(f: Flag) -> Flag:
  read_long(make_short(f))

def handler(f: Flag) -> Res<&2,&1,Fault,Flag -> Flag>:
  match f:
    case Off{}: Fail{Invalid{}}
    case On{}: Done{invert}

def run(r: Res<&2,&1,Fault,Flag -> Flag>, x: Flag) -> Flag:
  match r:
    case Fail{e}: x
    case Done{h}: h(x)

def arrow(f: Flag, x: Flag) -> Flag:
  run(handler(f),x)

def arrow_done(f: Flag) -> Flag:
  done(&2,&1,Fault,Flag -> Flag,handler(f))

def main() -> Flag:
  shared(On{},On{})
