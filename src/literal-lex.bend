import Base
import ./syntax.bend as S
import ./lex.bend as L
import ./literal.bend as Q

# The original lexer remains the enum profile's entry. Imported books opt in
# here; outside quoted tokens both entries share the same transition function.
def quoted_mode(mode: L.Mode) -> Bool:
  match mode:
    case L.Comment{}: False{}
    case _: True{}

def flush(state: L.State) -> Result<S.Error,L.State>:
  match state:
    case L.State{+off,line,col,L.Word{start,first_line,first_col,rev},tokens}:
      S.bind(S.Token,L.State,L.lexeme(String.reverse(rev),S.At{start,off,first_line,first_col}),token =>
        Done{L.State{off,line,col,L.Space{},Con{token,tokens}}})
    case _: Done{state}

def advance(raw: String, state: L.State) -> L.State:
  match raw state:
    case SNil{} _: state
    case SCon{c,tail} L.State{off,+line,+col,mode,tokens}:
      +newline = Char.is_eq(c,'\n')
      advance(tail,L.State{U32.add(off,1),Bool.pick(U32,newline,U32.add(line,1),line),Bool.pick(U32,newline,0,U32.add(col,1)),mode,tokens})

def emit(raw: String, state: L.State, origin: L.State) -> L.State:
  match state origin:
    case L.State{+end,line,col,mode,tokens} L.State{start,first_line,first_col,old,ignored}:
      L.State{end,line,col,L.Space{},Con{S.Token{raw,S.At{start,end,first_line,first_col}},tokens}}

def accepted(value: Q.Quoted, +state: L.State, +fuel: Nat,
  next: Nat -> String -> L.State -> Result<S.Error,List<&2,S.Token>>) -> Result<S.Error,List<&2,S.Token>>:
  match value state:
    case Q.Quoted{text,rest,+raw} L.State{+off,line,col,mode,tokens}:
      +size = String.length(raw)
      S.choose(Result<S.Error,List<&2,S.Token>>,Bool.and(Nat.is_le(size,fuel),Nat.is_le(size,U32.to_nat(U32.sub(65536,off)))),u =>
        S.bind(L.State,List<&2,S.Token>,flush(state),flushed =>
          next(Nat.sub(fuel,size),rest,emit(raw,advance(raw,flushed),state))),u =>
        Fail{S.Exhausted{"lex",S.At{off,off,line,col}}})

def scan(fuel: Nat, +budget: Nat, input: String, +state: L.State) -> Result<S.Error,List<&2,S.Token>>:
  match fuel input state:
    case _ SNil{} _: S.bind(List<&2,S.Token>,List<&2,S.Token>,L.finish(state),tokens => Q.floats(tokens))
    case 0n _ L.State{+off,line,col,mode,tokens}:
      Fail{S.Exhausted{"lex",S.At{off,off,line,col}}}
    case 1n+ +n SCon{+c,+tail} L.State{+off,+line,+col,mode,tokens}:
      S.choose(Result<S.Error,List<&2,S.Token>>,Bool.and(quoted_mode(mode),Bool.or(Char.is_eq(c,'\''),Char.is_eq(c,'"'))),u =>
        S.bind(Q.Quoted,List<&2,S.Token>,Q.quoted(SCon{c,tail},S.Token{"",S.At{off,U32.add(off,1),line,col}}),value =>
          accepted(value,state,budget,remaining => rest => after => scan(n,remaining,rest,after))),u =>
        S.choose(Result<S.Error,List<&2,S.Token>>,Nat.is_eq(budget,0n),u => Fail{S.Exhausted{"lex",S.At{off,off,line,col}}},u =>
          S.bind(L.State,List<&2,S.Token>,L.step(c,state),after => scan(n,Nat.sub(budget,1n),tail,after))))

def tokenize(+fuel: Nat, input: String) -> Result<S.Error,List<&2,S.Token>>:
  scan(fuel,fuel,input,L.State{0,1,0,L.Space{},Nil{}})
