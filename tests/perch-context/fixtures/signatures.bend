import Base

def Tag(c: Char) -> Type: U32

def choose(b: Bool, x: U32, y: U32) -> U32:
  match b:
    case False{}: y
    case True{}: x

def classify(+c: Char) -> Tag('''):
  choose(Char.is_eq(c, ')'), 31337, choose(Char.is_eq(c, ':'), 4242, 0))

def parameter(x: Tag(''')) -> U32: x
def markers(x: Tag(')'), y: Tag(':')) -> Tag(':'): (x + y : U32)
def unicode(x: Tag('🪞')) -> Tag('\u{1F600}'): x
def escaped(x: Tag('\'')) -> Tag('\\'): x
def apostrophe() -> Char: '''

def width(n: U32) -> U32: (n + 7 : U32)
def konst(n: U32) -> @m: U32 -> U32: m => (m + 90210 : U32)
def pair(n: U32) -> &k: U32 -> {k == width(n) : U32}: (width(n), {==})
