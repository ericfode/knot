type Flag is Type:
  Off{}
  On{}

type Pair is Type:
  P{fst: Flag, snd: Flag}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def g(p: Pair) -> Flag:
  match p:
    case P{flip, b}: flip(b)
