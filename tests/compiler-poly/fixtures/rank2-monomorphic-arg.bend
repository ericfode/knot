# A monomorphic Flag -> Flag where the rank-2 @-A: Type -> A -> A is expected.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}
  Gray{}

type Fault is Data:
  Invalid{}
  Unsupported{}

type Op<-R: Type> is Type:
  Emit{value: R}
  Halt{code: Fault}

def paint(f: Flag) -> Color:
  match f:
    case Off{}: Red{}
    case On{}: Blue{}

def colored(o: Op<Color>) -> Color:
  match o:
    case Emit{c}: c
    case Halt{e}: Gray{}

def run_flag(m: @-R: Type -> @k: (Flag -> Op<R>) -> Op<R>) -> Color:
  colored(m(Color,x => Emit{paint(x)}))

def direct(x: Flag) -> Color:
  run_flag(R => k => k(x))

def halted(x: Flag) -> Color:
  run_flag(R => k => Halt{Invalid{}})

def ident(-A: Type, x: A) -> A:
  x

def apply_poly(f: @-A: Type -> A -> A, x: Flag) -> Flag:
  f(Flag,x)

def by_def(x: Flag) -> Flag:
  apply_poly(ident,x)

def by_lambda(x: Flag) -> Flag:
  apply_poly(A => y => y,x)

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def by_mono(x: Flag) -> Flag:
  apply_poly(invert,x)

def main() -> Color:
  direct(On{})
