import Base

type Input is Data:
  LetX{}
  Single{}
  Lead{}
  Hashed{}
  Dotted{}

type Lexed is Data:
  Let{}
  Ex{}
  Silent{}
  Ab{}
  Path{}
  Unknown{}

def input(i: Input) -> String:
  match i:
    case LetX{}: "let x"
    case Single{}: "x"
    case Lead{}: " lead"
    case Hashed{}: "ab#c"
    case Dotted{}: "a.b c"

def alpha(+c: U32) -> Bool:
  Bool.or(U32.is_eq(c, 95), Bool.or(
    Bool.and(U32.is_ge(c, 65), U32.is_le(c, 90)),
    Bool.and(U32.is_ge(c, 97), U32.is_le(c, 122))))

def digit(+c: U32) -> Bool:
  Bool.and(U32.is_ge(c, 48), U32.is_le(c, 57))

def word(+c: U32) -> Bool:
  Bool.or(alpha(c), Bool.or(digit(c), U32.is_eq(c, 46)))

# lex.step_at keeps a word reversed, SCon{c, rev}; lex.finish restores it.
def gather(input: String, +rev: String) -> String:
  match input:
    case SNil{}: String.reverse(rev)
    case SCon{+c, tail}:
      Bool.pick(String, word(Char.to_u32(c)), gather(tail, SCon{c, rev}), String.reverse(rev))

def lexed(+w: String) -> Lexed:
  Bool.pick(Lexed, String.eq(w, "let"), Let{},
  Bool.pick(Lexed, String.eq(w, "x"), Ex{},
  Bool.pick(Lexed, String.eq(w, ""), Silent{},
  Bool.pick(Lexed, String.eq(w, "ab"), Ab{},
  Bool.pick(Lexed, String.eq(w, "a.b"), Path{}, Unknown{})))))

def first(i: Input) -> Lexed:
  lexed(gather(input(i), ""))

def main() -> Lexed:
  first(Dotted{})
