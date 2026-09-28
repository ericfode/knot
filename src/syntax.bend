import Base

type At is Data:
  At{start: U32, end: U32, line: U32, column: U32}

type Error is Data:
  Invalid{phase: String, code: String, at: At}
  Unsupported{phase: String, code: String, at: At}
  Exhausted{phase: String, at: At}
  Internal{phase: String, code: String}
  Host{phase: String, code: String}

type Token is Data:
  Token{text: String, at: At}

# The parser has a single recursive tree. Declaration/sequence variants never
# appear in checked expressions; the resolver validates that invariant.
# Matrix and Alias are internal lowering states, never parsed source forms.
type Node is Data:
  Variable{token: Token}
  Promotion{token: Token}
  Constructor{token: Token, arguments: List<&2,Node>}
  Call{token: Token, arguments: List<&2,Node>}
  Binding{token: Token, quantity: U32, annotation: Maybe<&2,Token>, value: Node, body: Node}
  Match{token: Token, value: Node, arms: List<&2,Node>}
  Arm{token: Token, pattern: Node, body: Node}
  Matrix{token: Token, columns: List<&2,Node>, rows: List<&2,Node>, work: U32}
  Alias{token: Token, level: U32, mark: U32, body: Node}
  Parameter{token: Token, quantity: U32, type_name: Token}
  Datatype{token: Token, reusable: Bool, constructors: List<&2,Node>}
  Function{token: Token, parameters: List<&2,Node>, result: Token, body: Node}
  Sequence{items: List<&2,Node>}

def text(t: Token) -> String:
  match t:
    case Token{s,a}: s

def at(t: Token) -> At:
  match t:
    case Token{s,a}: a

def column(t: Token) -> U32:
  match t:
    case Token{s,At{lo,hi,line,col}}: col

def line(t: Token) -> U32:
  match t:
    case Token{s,At{lo,hi,line,col}}: line

def here(ts: List<&2,Token>) -> At:
  match ts:
    case Nil{}: At{0,0,0,0}
    case Con{h,t}: at(h)

def matches(t: Token, value: String) -> Bool:
  String.eq(text(t),value)

def alpha(+c: U32) -> Bool:
  Bool.or(U32.is_eq(c,95),Bool.or(
    Bool.and(U32.is_ge(c,65),U32.is_le(c,90)),
    Bool.and(U32.is_ge(c,97),U32.is_le(c,122))))

def digit(+c: U32) -> Bool:
  Bool.and(U32.is_ge(c,48),U32.is_le(c,57))

def word(+c: U32) -> Bool:
  Bool.or(alpha(c),Bool.or(digit(c),U32.is_eq(c,46)))

def reserved(+s: String) -> Bool:
  Bool.or(String.eq(s,"type"),Bool.or(String.eq(s,"def"),
    Bool.or(String.eq(s,"is"),Bool.or(String.eq(s,"Type"),
    Bool.or(String.eq(s,"Data"),Bool.or(String.eq(s,"match"),
    Bool.or(String.eq(s,"case"),Bool.or(String.eq(s,"import"),
    Bool.or(String.eq(s,"law"),Bool.or(String.eq(s,"do"),
    Bool.or(String.eq(s,"return"),Bool.or(String.eq(s,"for"),
    Bool.or(String.eq(s,"exs"),Bool.or(String.eq(s,"where"),
    Bool.or(String.eq(s,"Kind"),String.eq(s,"Quant"))))))))))))))))

def choose(-A: Type, condition: Bool, yes: Unit -> A, no: Unit -> A) -> A:
  match condition:
    case True{}: yes(Unit{})
    case False{}: no(Unit{})

def bind(-A: Data, -B: Data, result: Result<Error,A>, next: A -> Result<Error,B>) -> Result<Error,B>:
  match result:
    case Fail{e}: Fail{e}
    case Done{x}: next(x)

def identifier_text(+s: String) -> Bool:
  match s:
    case SNil{}: False{}
    case SCon{c,tail}: Bool.and(alpha(Char.to_u32(c)),Bool.not(reserved(s)))

def identifier(t: Token) -> Bool:
  identifier_text(text(t))

def skip_lines(ts: List<&2,Token>) -> List<&2,Token>:
  match ts:
    case Nil{}: Nil{}
    case Con{+h,+t}:
      choose(List<&2,Token>,matches(h,"\n"),u => skip_lines(t),u => Con{h,t})
