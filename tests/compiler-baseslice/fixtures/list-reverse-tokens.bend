import Base

type Token is Data:
  Token{text: String, at: U32}

type Pushed is Data:
  NoTokens{}
  OneToken{}
  ThreeTokens{}

type Place is Data:
  Front{}
  Middle{}
  Back{}

type Seen is Data:
  SeenEof{}
  SeenAlpha{}
  SeenBeta{}
  SeenGamma{}
  SeenNothing{}

# The lexer pushes tokens newest first.
def pushed(n: Pushed) -> List<&2, Token>:
  match n:
    case NoTokens{}: Nil{}
    case OneToken{}: Con{Token{"alpha", 0}, Nil{}}
    case ThreeTokens{}: Con{Token{"gamma", 12}, Con{Token{"beta", 6}, Con{Token{"alpha", 0}, Nil{}}}}

# lex.finish: push <eof>, then List.reverse at &2.
def finish(+off: U32, tokens: List<&2, Token>) -> List<&2, Token>:
  List.reverse(&2, Token, Con{Token{"<eof>", off}, tokens})

def rest(ts: List<&2, Token>) -> List<&2, Token>:
  match ts:
    case Nil{}: Nil{}
    case Con{h, t}: t

def named(+s: String) -> Seen:
  Bool.pick(Seen, String.eq(s, "<eof>"), SeenEof{},
  Bool.pick(Seen, String.eq(s, "alpha"), SeenAlpha{},
  Bool.pick(Seen, String.eq(s, "beta"), SeenBeta{},
  Bool.pick(Seen, String.eq(s, "gamma"), SeenGamma{}, SeenNothing{}))))

def seen(ts: List<&2, Token>) -> Seen:
  match ts:
    case Nil{}: SeenNothing{}
    case Con{Token{s, a}, t}: named(s)

def at(p: Place, n: Pushed) -> Seen:
  match p:
    case Front{}: seen(finish(18, pushed(n)))
    case Middle{}: seen(rest(finish(18, pushed(n))))
    case Back{}: seen(rest(rest(rest(finish(18, pushed(n))))))

def main() -> Seen:
  at(Middle{}, ThreeTokens{})
