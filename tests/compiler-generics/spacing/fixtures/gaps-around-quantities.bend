type Flag is Data:
  Off{}
  On{}

type Both is Kind( &2 ):
  Both{fst: Flag, snd: Flag}

def pick(a, x: Flag) -> Flag:
  x

def first(p: Both) -> Flag:
  match p:
    case Both{x,y}:
      pick( &2 , x)

def swap(x: Flag) -> Flag:
  first(Both{x,On{}})

def main() -> Flag:
  swap(Off{})
