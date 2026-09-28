# S.choose at the caller's rigid A: one generic pick, used at Flag, Color, an arrow and a Res instance.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Unit is Data:
  Unit{}

type Res<a, b, -E: Kind(a), -A: Kind(b)> is Kind(a <&> b):
  Fail{error: E}
  Done{value: A}

def choose(-A: Type, condition: Flag, yes: Unit -> A, no: Unit -> A) -> A:
  match condition:
    case On{}: yes(Unit{})
    case Off{}: no(Unit{})

def pick(-A: Type, c: Flag, x: A, y: A) -> A:
  choose(A,c,u => x,u => y)

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def keep(x: Flag) -> Flag:
  x

def settle(r: Res<Flag,Color>) -> Color:
  match r:
    case Fail{e}: Red{}
    case Done{c}: c

def flags(c: Flag, +x: Flag) -> Flag:
  pick(Flag,c,x,invert(x))

def colors(c: Flag, x: Color) -> Color:
  pick(Color,c,x,Red{})

def arrows(c: Flag, x: Flag) -> Flag:
  pick(Flag -> Flag,c,invert,keep)(x)

def results(c: Flag, x: Color) -> Color:
  settle(pick(Res<Flag,Color>,c,Done{x},Fail{On{}}))

def main() -> Color:
  results(On{},Blue{})
