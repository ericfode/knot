# Knot's S.choose and S.bind signatures over fixture types; A is erased and instantiated at a function type.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

type Unit is Data:
  Unit{}

type Res<-A: Data> is Data:
  Fail{}
  Done{value: A}

def choose(-A: Type, condition: Flag, yes: Unit -> A, no: Unit -> A) -> A:
  match condition:
    case On{}: yes(Unit{})
    case Off{}: no(Unit{})

def bind(-A: Data, -B: Data, result: Res<A>, next: A -> Res<B>) -> Res<B>:
  match result:
    case Fail{}: Fail{}
    case Done{x}: next(x)

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def xor(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: b
    case On{}: invert(b)

def shade(x: Flag) -> Color:
  match x:
    case Off{}: Green{}
    case On{}: Blue{}

def guard(x: Flag, y: Flag) -> Res<Flag>:
  match x:
    case Off{}: Fail{}
    case On{}: Done{y}

def settle(r: Res<Color>) -> Color:
  match r:
    case Fail{}: Red{}
    case Done{c}: c

def pick(c: Flag, x: Color) -> Color:
  choose(Color, c, u => x, u => Red{})

def pick_function(c: Flag, x: Flag) -> Flag:
  choose(Flag -> Flag, c, u => invert, u => y => y)(x)

def chain(a: Flag, b: Flag, c: Flag) -> Color:
  settle(bind(Flag, Color, guard(a, b), +x => bind(Flag, Color, guard(x, c), y => Done{shade(xor(x, y))})))

def main() -> Color:
  chain(On{}, On{}, Off{})
