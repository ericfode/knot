# The Base Maybe.map and Maybe.bind shapes: a, -A: Kind(a), -B: Kind(a), f: A -> B, at &2 data and &1 arrows.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}
  Gray{}

type Opt<a, -A: Kind(a)> is Kind(a):
  None{}
  Some{value: A}

def omap(a, -A: Kind(a), -B: Kind(a), f: A -> B, m: Opt<a, A>) -> Opt<a, B>:
  match m:
    case None{}: None{}
    case Some{x}: Some{f(x)}

def obind(a, -A: Kind(a), -B: Kind(a), m: Opt<a, A>, f: A -> Opt<a, B>) -> Opt<a, B>:
  match m:
    case None{}: None{}
    case Some{x}: f(x)

def paint(f: Flag) -> Color:
  match f:
    case Off{}: Red{}
    case On{}: Blue{}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def need(f: Flag) -> Opt<&2,Flag>:
  match f:
    case Off{}: None{}
    case On{}: Some{On{}}

def color_or(m: Opt<&2,Color>) -> Color:
  match m:
    case None{}: Gray{}
    case Some{c}: c

def handler(f: Flag) -> Opt<&1,Flag -> Color>:
  match f:
    case Off{}: None{}
    case On{}: Some{paint}

def use(m: Opt<&1,Flag -> Color>, x: Flag) -> Color:
  match m:
    case None{}: Gray{}
    case Some{h}: h(x)

def mapped(f: Flag) -> Color:
  color_or(omap(&2,Flag,Color,paint,need(f)))

def bound(f: Flag, g: Flag) -> Color:
  color_or(obind(&2,Flag,Color,need(f),x => omap(&2,Flag,Color,paint,need(g))))

def arrows(f: Flag, x: Flag) -> Color:
  use(omap(&1,Flag -> Color,Flag -> Color,h => y => h(invert(y)),handler(f)),x)

def main() -> Color:
  arrows(On{},Off{})
