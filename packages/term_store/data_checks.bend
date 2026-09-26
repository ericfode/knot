import Base
import ./main.bend as S
import ./payload.bend as P
import ./checks.bend as C

# Distinct non-scalar payloads exercise actual compiled generic specializations.
def term_eq(a: P.Term,b: P.Term) -> Bool:
  match a:
    case P.Atom{x}:
      match b:
        case P.Atom{y}: U32.is_eq(x,y)
        case P.ApplyTerm{f,x}: False{}
    case P.ApplyTerm{f,x}:
      match b:
        case P.Atom{y}: False{}
        case P.ApplyTerm{g,y}: Bool.and(C.id_eq(f,g),C.id_eq(x,y))

def list_eq(xs: List<P.Term>,ys: List<P.Term>) -> Bool:
  match xs:
    case Nil{}:
      match ys:
        case Nil{}: True{}
        case Con{y,rest}: False{}
    case Con{x,rest}:
      match ys:
        case Nil{}: False{}
        case Con{y,tail}: Bool.and(term_eq(x,y),list_eq(rest,tail))

def store_terms() -> Bool:
  list_eq(P.term_witness(),[P.Atom{17},P.Atom{43},P.ApplyTerm{S.Id{23,0},S.Id{23,1}}])

def terminal(r: Result<S.Error,Result<String,P.Term>>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{x}:
      match x:
        case Fail{e}: False{}
        case Done{t}: term_eq(t,P.ApplyTerm{S.Id{5,2},S.Id{5,3}})

def observed(p: S.Memo<P.Term,String> & Result<S.Error,Result<String,P.Term>>) -> Bool:
  (m,r) = p
  terminal(r)

def finished(id: S.Id,p: S.Memo<P.Term,String> & Result<S.Error,Unit>) -> Bool:
  (m,r) = p
  Bool.and(C.unit_eq(r,Done{Unit{}}),observed(S.Memo.result(P.Term,String,m,id)))

def begun(+id: S.Id,p: S.Memo<P.Term,String> & Result<S.Error,Unit>) -> Bool:
  (m,r) = p
  Bool.and(C.unit_eq(r,Done{Unit{}}),finished(id,S.Memo.succeed(P.Term,String,m,id,P.ApplyTerm{S.Id{5,2},S.Id{5,3}})))

def allocated(p: S.Memo<P.Term,String> & Result<S.Error,S.Id>) -> Bool:
  (m,r) = p
  match r:
    case Fail{e}: False{}
    case Done{+id}: begun(id,S.Memo.begin(P.Term,String,m,id))

def ready(r: Result<S.Error,S.Memo<P.Term,String>>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{m}: allocated(S.Memo.alloc(P.Term,String,m))

def created(p: S.Scopes & Result<S.Error,S.Memo<P.Term,String>>) -> Bool:
  (scopes,r) = p
  ready(r)

def memo_terms() -> Bool:
  created(S.Memo.new(P.Term,String,S.Scopes.from(5),1))
