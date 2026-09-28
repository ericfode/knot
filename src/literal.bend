import Base
import ./syntax.bend as S

type Glyph is Data:
  Glyph{code: U32, rest: String, raw: String}
type Quoted is Data:
  Quoted{value: List<&2,U32>, rest: String, raw: String}

def invalid(-A: Type, +token: S.Token, code: String) -> Result<S.Error,A>:
  Fail{S.Invalid{"lex",code,S.at(token)}}

def hex(+c: U32) -> Maybe<&2,U32>:
  S.choose(Maybe<&2,U32>,S.digit(c),u => Some{U32.sub(c,48)},u =>
  S.choose(Maybe<&2,U32>,Bool.and(U32.is_ge(c,65),U32.is_le(c,70)),u => Some{U32.sub(c,55)},u =>
  S.choose(Maybe<&2,U32>,Bool.and(U32.is_ge(c,97),U32.is_le(c,102)),u => Some{U32.sub(c,87)},u => None{})))

def escape(c: Char) -> Maybe<&2,U32>:
  match c:
    case '\\': Some{92}
    case '\'': Some{39}
    case '"': Some{34}
    case 'n': Some{10}
    case 't': Some{9}
    case 'r': Some{13}
    case '0': Some{0}
    case _: None{}

def escaped(value: Maybe<&2,U32>, rest: String, raw: String, token: S.Token) -> Result<S.Error,Glyph>:
  match value:
    case None{}: invalid(Glyph,token,"escape")
    case Some{code}: Done{Glyph{code,rest,raw}}

def unicode_digit(value: Maybe<&2,U32>, +token: S.Token, next: U32 -> Result<S.Error,Glyph>) -> Result<S.Error,Glyph>:
  match value:
    case None{}: invalid(Glyph,token,"unicode-escape")
    case Some{digit}: next(digit)

def unicode(input: String, +count: U32, +code: U32, +raw: String, +token: S.Token) -> Result<S.Error,Glyph>:
  match input:
    case SNil{}: invalid(Glyph,token,"unicode-escape")
    case SCon{+c,+tail}:
      S.choose(Result<S.Error,Glyph>,Char.is_eq(c,'}'),u =>
        S.choose(Result<S.Error,Glyph>,U32.is_gt(count,0),u => Done{Glyph{code,tail,String.append(raw,"}")}},u => invalid(Glyph,token,"unicode-escape")),u =>
      S.choose(Result<S.Error,Glyph>,U32.is_lt(count,8),u =>
        unicode_digit(hex(Char.to_u32(c)),token,digit => unicode(tail,U32.add(count,1),U32.add(U32.mul(code,16),digit),String.append(raw,SCon{c,SNil{}}),token)),u => invalid(Glyph,token,"unicode-escape")))

def glyph(input: String, +token: S.Token) -> Result<S.Error,Glyph>:
  match input:
    case SCon{'\\',SCon{+u,SCon{'{',+tail}}}:
      S.choose(Result<S.Error,Glyph>,Bool.or(Char.is_eq(u,'u'),Char.is_eq(u,'U')),x =>
        unicode(tail,0,0,String.concat(["\\",SCon{u,SNil{}},"{"]),token),x => invalid(Glyph,token,"escape"))
    case SCon{'\\',SCon{+c,tail}}:
      escaped(escape(c),tail,SCon{'\\',SCon{c,SNil{}}},token)
    case SCon{+c,tail}:
      S.choose(Result<S.Error,Glyph>,U32.is_gt(Char.to_u32(c),126),u =>
        Fail{S.Unsupported{"lex","non-ascii",S.at(token)}},u => Done{Glyph{Char.to_u32(c),tail,SCon{c,SNil{}}}})
    case SNil{}: invalid(Glyph,token,"unclosed-literal")

def then(result: Result<S.Error,Glyph>, next: U32 -> String -> String -> Result<S.Error,Quoted>) -> Result<S.Error,Quoted>:
  match result:
    case Fail{error}: Fail{error}
    case Done{Glyph{code,rest,raw}}: next(code,rest,raw)

def close_char(rest: String, code: U32, raw: String, token: S.Token) -> Result<S.Error,Quoted>:
  match rest:
    case SCon{'\'',tail}: Done{Quoted{[code],tail,String.concat(["'",raw,"'"])}}
    case _: invalid(Quoted,token,"char-width")

def quoted_text(fuel: Nat, input: String, +value: List<&2,U32>, +raw: String, +token: S.Token) -> Result<S.Error,Quoted>:
  match fuel input:
    case _ SCon{'"',tail}: Done{Quoted{List.reverse(&2,U32,value),tail,String.append(String.reverse(raw),"\"")}}
    case _ SNil{}: invalid(Quoted,token,"unclosed-literal")
    case 0n _: Fail{S.Exhausted{"lex",S.at(token)}}
    case 1n+n _:
      then(glyph(input,token),c => tail => taken =>
        quoted_text(n,tail,Con{c,value},String.append(String.reverse(taken),raw),token))

def quoted(input: String, +token: S.Token) -> Result<S.Error,Quoted>:
  match input:
    case SCon{'"',tail}: quoted_text(65536n,tail,Nil{},"\"",token)
    case SCon{'\'',tail}: then(glyph(tail,token),c => rest => raw => close_char(rest,c,raw,token))
    case _: invalid(Quoted,token,"literal-prefix")

def numeric(text: String) -> Bool:
  match text:
    case SCon{c,tail}: S.digit(Char.to_u32(c))
    case _: False{}

def starts(text: String) -> Bool:
  match text:
    case SCon{+c,tail}: Bool.or(S.digit(Char.to_u32(c)),Bool.or(Char.is_eq(c,'\''),Char.is_eq(c,'"')))
    case _: False{}

def decimal(text: String, +value: U32, +token: S.Token) -> Result<S.Error,U32>:
  match text:
    case SNil{}: Done{value}
    case SCon{+c,+tail}:
      +digit = U32.sub(Char.to_u32(c),48)
      S.choose(Result<S.Error,U32>,S.digit(Char.to_u32(c)),u =>
      S.choose(Result<S.Error,U32>,Bool.or(U32.is_lt(value,429496729),Bool.and(U32.is_eq(value,429496729),U32.is_le(digit,5))),u =>
        decimal(tail,U32.add(U32.mul(value,10),digit),token),u => invalid(U32,token,"literal-overflow")),u => invalid(U32,token,"decimal-literal"))

def first(text: String) -> U32:
  match text:
    case SCon{c,tail}: Char.to_u32(c)
    case SNil{}: 0

def first_code(codes: List<&2,U32>) -> U32:
  match codes:
    case Nil{}: 0
    case Con{head,tail}: head

def decoded(value: Quoted, +token: S.Token) -> Result<S.Error,S.Node>:
  match value:
    case Quoted{+text,rest,raw}:
      Done{S.Literal{token,Bool.pick(U32,U32.is_eq(first(S.text(token)),39),2,3),first_code(text),text}}

def parse(+token: S.Token) -> Result<S.Error,S.Node>:
  +text = S.text(token)
  S.choose(Result<S.Error,S.Node>,numeric(text),u =>
    +nat = String.ends_with(text,"n")
    +digits = S.choose(String,nat,u => String.take(text,Nat.sub(String.length(text),1n)),u => text)
    S.bind(U32,S.Node,decimal(digits,0,token),value => Done{S.Literal{token,Bool.pick(U32,nat,1,0),value,Nil{}}}),u =>
    S.bind(Quoted,S.Node,quoted(text,token),value => decoded(value,token)))

def float_scan(tokens: List<&2,S.Token>, reversed: List<&2,S.Token>) -> Result<S.Error,List<&2,S.Token>>:
  match tokens:
    case Nil{}: Done{List.reverse(&2,S.Token,reversed)}
    case Con{+h,+tail}:
      S.choose(Result<S.Error,List<&2,S.Token>>,Bool.and(numeric(S.text(h)),String.contains(S.text(h),".")),u =>
        Fail{S.Unsupported{"lex","f32-literal",S.at(h)}},u =>
        float_scan(tail,Con{h,reversed}))

def floats(tokens: List<&2,S.Token>) -> Result<S.Error,List<&2,S.Token>>:
  float_scan(tokens,Nil{})

def children(node: S.Node) -> List<&2,S.Node>:
  match node:
    case S.Constructor{token,args}: args
    case S.Call{token,args}: args
    case S.Binding{token,q,typ,value,body}: [value,body]
    case S.Match{token,value,arms}: Con{value,arms}
    case S.Arm{token,pattern,body}: [pattern,body]
    case S.Datatype{token,data,constructors}: constructors
    case S.Function{token,params,result,body}: List.append(&2,S.Node,params,[body])
    case S.Sequence{items}: items
    case _: Nil{}

# The single-file interface retains its original capability boundary. Parsing
# a token is separate from accepting it in that execution profile.
def legacy(fuel: Nat, pending: List<&2,S.Node>) -> Result<S.Error,Unit>:
  match fuel pending:
    case _ Nil{}: Done{Unit{}}
    case 0n _: Fail{S.Exhausted{"parse",S.At{0,0,0,0}}}
    case 1n+n Con{S.Literal{token,kind,number,codes},tail}:
      Fail{S.Unsupported{"parse","term-form",S.at(token)}}
    case 1n+n Con{S.Offset{token,count,value},tail}:
      Fail{S.Unsupported{"parse","term-form",S.at(token)}}
    case 1n+n Con{S.Intrinsic{token,op,args},tail}:
      Fail{S.Unsupported{"parse","term-form",S.at(token)}}
    case 1n+n Con{head,tail}:
      legacy(n,List.append(&2,S.Node,children(head),tail))
