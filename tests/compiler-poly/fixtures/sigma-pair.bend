# The Base Pair shape outside Base: Both(A,B) is a fixture Sigma with family _ => B, destructured by let and by match.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Dep<a, b, -A: Kind(a), -B: @-x: A -> Kind(b)> is Kind(a <&> b):
  Pack{fst: A, snd: B(fst)}

def Both(-A: Type, -B: Type) -> Type:
  Dep<&1,&1,A,_ => B>

def swap(p: Both(Flag,Color)) -> Both(Color,Flag):
  Pack{f,c} = p
  Pack{c,f}

def snd_flag(p: Both(Color,Flag)) -> Flag:
  match p:
    case Pack{c,f}: f

def fst_color(p: Both(Color,Flag)) -> Color:
  Pack{c,f} = p
  c

def run_pair(p: Both(Flag -> Flag,Flag)) -> Flag:
  Pack{g,x} = p
  g(x)

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def flag_of(f: Flag, c: Color) -> Flag:
  snd_flag(swap(Pack{f,c}))

def color_of(f: Flag, c: Color) -> Color:
  fst_color(swap(Pack{f,c}))

def applied(x: Flag) -> Flag:
  run_pair(Pack{invert,x})

def main() -> Color:
  color_of(On{},Blue{})
