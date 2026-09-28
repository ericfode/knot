import Base

# One Char on each side of every range syntax.bend tests, plus two codes
# past 2^31 that a signed comparison would misread as small.
type Probe is Data:
  At{}
  UpperA{}
  UpperZ{}
  Bracket{}
  Backtick{}
  LowerA{}
  LowerZ{}
  Brace{}
  Slash{}
  DigitZero{}
  DigitNine{}
  Colon{}
  Underscore{}
  Period{}
  Minus{}
  Separator{}
  Space{}
  High{}
  Top{}

type Shape is Data:
  Alpha{}
  Digit{}
  Joiner{}
  Other{}
  Wide{}

type Verdict is Data:
  No{}
  Yes{}

def probe(p: Probe) -> Char:
  match p:
    case At{}: '@'
    case UpperA{}: 'A'
    case UpperZ{}: 'Z'
    case Bracket{}: '['
    case Backtick{}: '`'
    case LowerA{}: 'a'
    case LowerZ{}: 'z'
    case Brace{}: '{'
    case Slash{}: '/'
    case DigitZero{}: '0'
    case DigitNine{}: '9'
    case Colon{}: ':'
    case Underscore{}: '_'
    case Period{}: '.'
    case Minus{}: '-'
    case Separator{}: '\u{1f}'
    case Space{}: ' '
    case High{}: '\u{80000000}'
    case Top{}: '\u{ffffffff}'

def alpha(+c: U32) -> Bool:
  Bool.or(U32.is_eq(c, 95), Bool.or(
    Bool.and(U32.is_ge(c, 65), U32.is_le(c, 90)),
    Bool.and(U32.is_ge(c, 97), U32.is_le(c, 122))))

def digit(+c: U32) -> Bool:
  Bool.and(U32.is_ge(c, 48), U32.is_le(c, 57))

def word(+c: U32) -> Bool:
  Bool.or(alpha(c), Bool.or(digit(c), U32.is_eq(c, 46)))

def shape_code(+c: U32) -> Shape:
  Bool.pick(Shape, U32.is_gt(c, 126), Wide{},
  Bool.pick(Shape, alpha(c), Alpha{},
  Bool.pick(Shape, digit(c), Digit{},
  Bool.pick(Shape, word(c), Joiner{}, Other{}))))

def verdict(b: Bool) -> Verdict:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def shape(p: Probe) -> Shape:
  shape_code(Char.to_u32(probe(p)))

# lex.normal's control test: below 32, unsigned.
def control(p: Probe) -> Verdict:
  verdict(U32.is_lt(Char.to_u32(probe(p)), 32))

def main() -> Shape:
  shape(High{})
