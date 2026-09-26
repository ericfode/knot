import Base
import ./main.bend as S

# Generic 3-cell growth/write observation, quantified over arbitrary Data payloads.
def values(-T: Data,p: S.Store<T> & List<T>) -> List<T>:
  (s,xs) = p
  xs

def written(-T: Data,p: S.Store<T> & Result<S.Error,Unit>) -> List<T>:
  (s,r) = p
  values(T,S.Store.snapshot(T,s))

def third(-T: Data,x: T,p: S.Store<T> & Result<S.Error,S.Id>) -> List<T>:
  (s,r) = p
  written(T,S.Store.set(T,s,S.Id{23,1},x))

def second(-T: Data,c: T,x: T,p: S.Store<T> & Result<S.Error,S.Id>) -> List<T>:
  (s,r) = p
  third(T,x,S.Store.alloc(T,s,c))

def first(-T: Data,b: T,c: T,x: T,p: S.Store<T> & Result<S.Error,S.Id>) -> List<T>:
  (s,r) = p
  second(T,c,x,S.Store.alloc(T,s,b))

def ready(-T: Data,a: T,b: T,c: T,x: T,r: Result<S.Error,S.Store<T>>) -> List<T>:
  match r:
    case Fail{e}: Nil{}
    case Done{s}: first(T,b,c,x,S.Store.alloc(T,s,a))

def created(-T: Data,a: T,b: T,c: T,x: T,p: S.Scopes & Result<S.Error,S.Store<T>>) -> List<T>:
  (scopes,r) = p
  ready(T,a,b,c,x,r)

def preserved(-T: Data,a: T,b: T,c: T,x: T) -> List<T>:
  created(T,a,b,c,x,S.Store.new(T,S.Scopes.from(23),3))

type Term is Data:
  Atom{value: U32}
  ApplyTerm{fun: S.Id,arg: S.Id}

def term_witness() -> List<Term>:
  preserved(Term,Atom{17},Atom{29},ApplyTerm{S.Id{23,0},S.Id{23,1}},Atom{43})
