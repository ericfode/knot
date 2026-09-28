# Dep at &2,&2 is Data: a + pair is destructured twice, and Seq<&2,Dep<..>> is the Map.to_list entry shape.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Dep<a, b, -A: Kind(a), -B: @-x: A -> Kind(b)> is Kind(a <&> b):
  Pack{fst: A, snd: B(fst)}

type Seq<a, -A: Kind(a)> is Kind(a):
  Stop{}
  Link{head: A, tail: Seq<a, A>}

def key(p: Dep<&2,&2,Flag,_ => Color>) -> Flag:
  match p:
    case Pack{f,c}: f

def val(p: Dep<&2,&2,Flag,_ => Color>) -> Color:
  match p:
    case Pack{f,c}: c

def gate(f: Flag, c: Color) -> Color:
  match f:
    case Off{}: Red{}
    case On{}: c

def shared(f: Flag, c: Color) -> Color:
  +p : Dep<&2,&2,Flag,_ => Color> = Pack{f,c}
  gate(key(p),val(p))

def lookup(entries: Seq<&2,Dep<&2,&2,Flag,_ => Color>>, k: Flag) -> Color:
  match entries:
    case Stop{}: Red{}
    case Link{+e,t}:
      match k:
        case Off{}: val(e)
        case On{}: gate(key(e),val(e))

def entry(f: Flag, c: Color) -> Color:
  lookup(Link{Pack{f,c},Stop{}},On{})

def main() -> Color:
  shared(On{},Blue{})
