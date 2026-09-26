import Base
import ./syntax.bend as S

type Mode is Data:
  Space{}
  Comment{}
  Word{start: U32, line: U32, column: U32, reversed: String}

type State is Data:
  State{offset: U32, line: U32, column: U32, mode: Mode, tokens: List<&2,S.Token>}

def normal(+c: Char, +off: U32, +line: U32, +col: U32,
  +tokens: List<&2,S.Token>) -> Result<S.Error,State>:
  +code = Char.to_u32(c)
  +next = U32.add(off,1)
  +a : S.At = S.At{off,next,line,col}
  S.choose(Result<S.Error,State>,U32.is_eq(code,10),u =>
    Done{State{next,U32.add(line,1),0,Space{},Con{S.Token{"\n",a},tokens}}},u =>
  S.choose(Result<S.Error,State>,U32.is_eq(code,32),u =>
    Done{State{next,line,U32.add(col,1),Space{},tokens}},u =>
  S.choose(Result<S.Error,State>,U32.is_eq(code,35),u =>
    Done{State{next,line,U32.add(col,1),Comment{},tokens}},u =>
  S.choose(Result<S.Error,State>,Bool.or(U32.is_eq(code,9),U32.is_eq(code,13)),u =>
    Fail{S.Unsupported{"lex","whitespace",a}},u =>
  S.choose(Result<S.Error,State>,Bool.or(U32.is_eq(code,34),U32.is_eq(code,39)),u =>
    Fail{S.Unsupported{"lex","literal",a}},u =>
  S.choose(Result<S.Error,State>,U32.is_gt(code,126),u =>
    Fail{S.Unsupported{"lex","non-ascii",a}},u =>
  S.choose(Result<S.Error,State>,U32.is_lt(code,32),u =>
    Fail{S.Invalid{"lex","control-character",a}},u =>
  S.choose(Result<S.Error,State>,S.word(code),u =>
    Done{State{next,line,U32.add(col,1),Word{off,line,col,SCon{c,SNil{}}},tokens}},u =>
    Done{State{next,line,U32.add(col,1),Space{},Con{S.Token{SCon{c,SNil{}},a},tokens}}}))))))))

def step_at(+c: Char, state: State) -> Result<S.Error,State>:
  match state:
    case State{+off,+line,+col,Space{},tokens}:
      normal(c,off,line,col,tokens)
    case State{+off,+line,+col,Comment{},+tokens}:
      S.choose(Result<S.Error,State>,Char.is_eq(c,'\n'),u => normal(c,off,line,col,tokens),u =>
      S.choose(Result<S.Error,State>,U32.is_gt(Char.to_u32(c),126),u =>
        Fail{S.Unsupported{"lex","non-ascii",S.At{off,U32.add(off,1),line,col}}},u =>
        Done{State{U32.add(off,1),line,U32.add(col,1),Comment{},tokens}}))
    case State{+off,+line,+col,Word{+start,+first_line,+first_col,+rev},+tokens}:
      S.choose(Result<S.Error,State>,S.word(Char.to_u32(c)),u =>
        Done{State{U32.add(off,1),line,U32.add(col,1),Word{start,first_line,first_col,SCon{c,rev}},tokens}},u =>
        normal(c,off,line,col,Con{S.Token{String.reverse(rev),S.At{start,off,first_line,first_col}},tokens}))

def step(+c: Char, +state: State) -> Result<S.Error,State>:
  match state:
    case State{+off,line,col,mode,tokens}:
      S.choose(Result<S.Error,State>,U32.is_lt(off,65536),u => step_at(c,state),u =>
        Fail{S.Exhausted{"lex",S.At{off,off,line,col}}})

def finish(state: State) -> List<&2,S.Token>:
  match state:
    case State{+off,line,col,Space{},tokens}:
      List.reverse(&2,S.Token,Con{S.Token{"<eof>",S.At{off,off,line,col}},tokens})
    case State{+off,line,col,Comment{},tokens}:
      List.reverse(&2,S.Token,Con{S.Token{"<eof>",S.At{off,off,line,col}},tokens})
    case State{+off,line,col,Word{start,first_line,first_col,rev},tokens}:
      List.reverse(&2,S.Token,Con{S.Token{"<eof>",S.At{off,off,line,col}},
        Con{S.Token{String.reverse(rev),S.At{start,off,first_line,first_col}},tokens}})

# Fuel counts consumed characters, including whitespace and comments. The
# caller caps it below 2^32-1, keeping all offsets/line/column additions exact.
def scan(fuel: Nat, input: String, +state: State) -> Result<S.Error,List<&2,S.Token>>:
  match fuel input:
    case _ SNil{}: Done{finish(state)}
    case 0n SCon{c,tail}:
      match state:
        case State{+off,line,col,mode,tokens}:
          Fail{S.Exhausted{"lex",S.At{off,off,line,col}}}
    case 1n+n SCon{c,tail}:
      S.bind(State,List<&2,S.Token>,step(c,state),next => scan(n,tail,next))

def tokenize(fuel: Nat, input: String) -> Result<S.Error,List<&2,S.Token>>:
  scan(fuel,input,State{0,1,0,Space{},Nil{}})
