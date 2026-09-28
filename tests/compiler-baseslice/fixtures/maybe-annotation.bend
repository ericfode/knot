import Base

type Token is Data:
  Token{text: String}

# syntax.Node's Binding keeps an optional annotation: Maybe<&2, Token>.
type Binding is Data:
  Binding{name: Token, annotation: Maybe<&2, Token>, value: Token}

type Form is Data:
  Bare{}
  Annotated{}

type Named is Data:
  FlagType{}
  ColorType{}

type Seen is Data:
  Unannotated{}
  SeenFlag{}
  SeenOther{}

def type_name(n: Named) -> Token:
  match n:
    case FlagType{}: Token{"Flag"}
    case ColorType{}: Token{"Color"}

def binding(f: Form, n: Named) -> Binding:
  match f:
    case Bare{}: Binding{Token{"x"}, None{}, Token{"On"}}
    case Annotated{}: Binding{Token{"x"}, Some{type_name(n)}, Token{"On"}}

def named(t: Token) -> Seen:
  match t:
    case Token{s}: Bool.pick(Seen, String.eq(s, "Flag"), SeenFlag{}, SeenOther{})

def seen(a: Maybe<&2, Token>) -> Seen:
  match a:
    case None{}: Unannotated{}
    case Some{t}: named(t)

def inspect(b: Binding) -> Seen:
  match b:
    case Binding{name, a, value}: seen(a)

def annotation(f: Form, n: Named) -> Seen:
  inspect(binding(f, n))

def main() -> Seen:
  annotation(Annotated{}, FlagType{})
