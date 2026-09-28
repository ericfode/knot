# The S.choose shape: -A: Type types both branch closures, nested, capturing the caller's locals.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Tick is Data:
  Tick{}

def choose(-A: Type, condition: Flag, yes: Tick -> A, no: Tick -> A) -> A:
  match condition:
    case On{}: yes(Tick{})
    case Off{}: no(Tick{})

def tint(c: Flag, +d: Color) -> Color:
  choose(Color,c,u => d,u => Red{})

def nest(c: Flag, g: Flag, +d: Color) -> Color:
  choose(Color,c,u => choose(Color,g,u => d,u => Blue{}),u => Red{})

def main() -> Color:
  nest(On{},On{},Red{})
