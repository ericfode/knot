import Base

type Sample is Data:
  KwType{}
  KwQuant{}
  KwUpper{}
  Typed{}
  Typ{}
  Blank{}
  Under{}
  Dotted{}
  Numeric{}

type Lexeme is Data:
  Keyword{}
  Name{}
  Other{}

def text(s: Sample) -> String:
  match s:
    case KwType{}: "type"
    case KwQuant{}: "Quant"
    case KwUpper{}: "Type"
    case Typed{}: "typed"
    case Typ{}: "typ"
    case Blank{}: ""
    case Under{}: "_x"
    case Dotted{}: "x.y"
    case Numeric{}: "9x"

def alpha(+c: U32) -> Bool:
  Bool.or(U32.is_eq(c, 95), Bool.or(
    Bool.and(U32.is_ge(c, 65), U32.is_le(c, 90)),
    Bool.and(U32.is_ge(c, 97), U32.is_le(c, 122))))

# syntax.reserved and syntax.identifier_text, verbatim.
def reserved(s: String) -> Bool:
  Bool.or(String.eq(s, "type"), Bool.or(String.eq(s, "def"),
    Bool.or(String.eq(s, "is"), Bool.or(String.eq(s, "Type"),
    Bool.or(String.eq(s, "Data"), Bool.or(String.eq(s, "match"),
    Bool.or(String.eq(s, "case"), Bool.or(String.eq(s, "import"),
    Bool.or(String.eq(s, "law"), Bool.or(String.eq(s, "do"),
    Bool.or(String.eq(s, "return"), Bool.or(String.eq(s, "for"),
    Bool.or(String.eq(s, "exs"), Bool.or(String.eq(s, "where"),
    Bool.or(String.eq(s, "Kind"), String.eq(s, "Quant"))))))))))))))))

def identifier_text(+s: String) -> Bool:
  match s:
    case SNil{}: False{}
    case SCon{c, tail}: Bool.and(alpha(Char.to_u32(c)), Bool.not(reserved(s)))

def lexeme(w: Sample) -> Lexeme:
  +s = text(w)
  Bool.pick(Lexeme, reserved(s), Keyword{},
    Bool.pick(Lexeme, identifier_text(s), Name{}, Other{}))

def main() -> Lexeme:
  lexeme(Typed{})
