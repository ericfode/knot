import Base
import ./syntax.bend as S
import ./core.bend as C
import ./lex.bend as L
import ./parse.bend as P
import ./check.bend as K
import ./diagnostic.bend as D

type Limits is Data:
  Limits{characters: Nat, parser: Nat, checker: Nat}

def fail(+error: S.Error) -> IO(Unit):
  IO.die(Unit,D.status(error),D.error(error))

def checked(result: Result<S.Error,C.Book>, next: C.Book -> IO(Unit)) -> IO(Unit):
  match result:
    case Fail{error}: fail(error)
    case Done{book}: next(book)

def parsed(limits: Limits, result: Result<S.Error,P.Parsed>, next: C.Book -> IO(Unit)) -> IO(Unit):
  match limits result:
    case Limits{chars,parser,checker} Done{P.Parsed{root,rest}}: checked(K.check(checker,root),next)
    case _ Fail{error}: fail(error)

def source(+limits: Limits, text: String, next: C.Book -> IO(Unit)) -> IO(Unit):
  match limits:
    case Limits{chars,+parser,checker}:
      parsed(limits,S.bind(List<&2,S.Token>,P.Parsed,L.tokenize(chars,text),tokens => P.parse(parser,tokens)),next)

def read_result(limits: Limits, result: Result<&1,&1,U32 & String,String>, next: C.Book -> IO(Unit)) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\tread\t",U32.show(code),"\t",message]))
    case Done{text}: source(limits,text,next)

def read_pair(limits: Limits, pair: File & Result<&1,&1,U32 & String,String>, next: C.Book -> IO(Unit)) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    read_result(limits,result,next)

def opened(limits: Limits, result: Result<&1,&1,U32 & String,File>, next: C.Book -> IO(Unit)) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\topen\t",U32.show(code),"\t",message]))
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,String>,Unit,File.read(file,65537),pair => read_pair(limits,pair,next))

def load(path: String, limits: Limits, next: C.Book -> IO(Unit)) -> IO(Unit):
  IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),result => opened(limits,result,next))

def natural(value: Maybe<&2,U32>, +cap: U32) -> Result<S.Error,Nat>:
  match value:
    case None{}: Fail{S.Host{"arguments","expected-u32"}}
    case Some{+x}:
      S.choose(Result<S.Error,Nat>,U32.is_le(x,cap),u => Done{U32.to_nat(x)},u => Fail{S.Host{"arguments","budget-out-of-range"}})

def ordinal(value: Maybe<&2,U32>) -> Result<S.Error,U32>:
  match value:
    case None{}: Fail{S.Host{"arguments","expected-u32"}}
    case Some{x}: Done{x}

def ordinals(values: List<String>) -> Result<S.Error,List<&2,U32>>:
  match values:
    case Nil{}: Done{Nil{}}
    case Con{head,tail}:
      S.bind(U32,List<&2,U32>,ordinal(U32.read(head)),x =>
        S.bind(List<&2,U32>,List<&2,U32>,ordinals(tail),xs => Done{Con{x,xs}}))
