import Base

type Glyph is Data:
  LowA{}
  LowB{}
  Wide{}

type Order is Data:
  Before{}
  Same{}
  After{}
  Broken{}

def glyph(g: Glyph) -> Char:
  match g:
    case LowA{}: 'a'
    case LowB{}: 'b'
    case Wide{}: '\u{80000000}'

def order(c: Cmp) -> Order:
  match c:
    case LT{}: Before{}
    case EQ{}: Same{}
    case GT{}: After{}

def intact(ok: Bool, o: Order) -> Order:
  match ok:
    case False{}: Broken{}
    case True{}: o

# Char.cmp hands both Chars back beside the order, as String.cmp.fin needs.
def settle(+a: Char, +b: Char, r: (Char & Char) & Cmp) -> Order:
  ((a2, b2), c) = r
  intact(Bool.and(Char.is_eq(a, a2), Char.is_eq(b, b2)), order(c))

def compare(l: Glyph, r: Glyph) -> Order:
  +a = glyph(l)
  +b = glyph(r)
  settle(a, b, Char.cmp(a, b))

def codes(l: Glyph, r: Glyph) -> Order:
  order(U32.cmp(Char.to_u32(glyph(l)), Char.to_u32(glyph(r))))

def main() -> Order:
  compare(Wide{}, LowA{})
