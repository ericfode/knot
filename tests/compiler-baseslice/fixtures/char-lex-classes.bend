import Base

type Sample is Data:
  Newline{}
  Blank{}
  Hash{}
  Tab{}
  Carriage{}
  Quote{}
  Apostrophe{}
  Tilde{}
  Delete{}
  Bell{}
  Letter{}
  Period{}
  Paren{}

type Class is Data:
  LineEnd{}
  Gap{}
  CommentStart{}
  BadSpace{}
  LiteralStart{}
  NonAscii{}
  Control{}
  WordChar{}
  Punct{}

type Verdict is Data:
  No{}
  Yes{}

def sample(s: Sample) -> Char:
  match s:
    case Newline{}: '\n'
    case Blank{}: ' '
    case Hash{}: '#'
    case Tab{}: '\t'
    case Carriage{}: '\r'
    case Quote{}: '"'
    case Apostrophe{}: '\''
    case Tilde{}: '~'
    case Delete{}: '\u{7f}'
    case Bell{}: '\u{7}'
    case Letter{}: 'q'
    case Period{}: '.'
    case Paren{}: '('

# syntax.alpha, syntax.digit and syntax.word, verbatim.
def alpha(+c: U32) -> Bool:
  Bool.or(U32.is_eq(c, 95), Bool.or(
    Bool.and(U32.is_ge(c, 65), U32.is_le(c, 90)),
    Bool.and(U32.is_ge(c, 97), U32.is_le(c, 122))))

def digit(+c: U32) -> Bool:
  Bool.and(U32.is_ge(c, 48), U32.is_le(c, 57))

def word(+c: U32) -> Bool:
  Bool.or(alpha(c), Bool.or(digit(c), U32.is_eq(c, 46)))

# lex.normal's dispatch order, with Bool.pick in place of S.choose.
def classify_code(+code: U32) -> Class:
  Bool.pick(Class, U32.is_eq(code, 10), LineEnd{},
  Bool.pick(Class, U32.is_eq(code, 32), Gap{},
  Bool.pick(Class, U32.is_eq(code, 35), CommentStart{},
  Bool.pick(Class, Bool.or(U32.is_eq(code, 9), U32.is_eq(code, 13)), BadSpace{},
  Bool.pick(Class, Bool.or(U32.is_eq(code, 34), U32.is_eq(code, 39)), LiteralStart{},
  Bool.pick(Class, U32.is_gt(code, 126), NonAscii{},
  Bool.pick(Class, U32.is_lt(code, 32), Control{},
  Bool.pick(Class, word(code), WordChar{}, Punct{}))))))))

def classify(s: Sample) -> Class:
  classify_code(Char.to_u32(sample(s)))

def verdict(b: Bool) -> Verdict:
  match b:
    case False{}: No{}
    case True{}: Yes{}

# lex.step_at in comment mode: only a newline ends the comment.
def ends_comment(s: Sample) -> Verdict:
  verdict(Char.is_eq(sample(s), '\n'))

def main() -> Class:
  classify(Hash{})
