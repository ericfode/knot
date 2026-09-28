type Flag is Data:
  Off{}
  On{}
type Pair is Data:
  Pair{left: Flag, right: Flag}
def first(+p: Pair) -> Flag:
  match p:
    case Pair{a,b}: a
def second(+p: Pair) -> Flag:
  match p:
    case Pair{a,b}: b
def choose(a: Flag, b: Flag) -> Flag:
  b
def observe(a: Flag, b: Flag) -> Flag:
  +p : Pair = Pair{a,b}
  x = first(p)
  y = second(p)
  choose(x,y)
def repeated() -> Flag:
  +a : Flag = On{}
  +p : Pair = Pair{a,a}
  x = first(p)
  y = second(p)
  choose(x,y)
def main() -> Flag:
  observe(Off{},On{})
