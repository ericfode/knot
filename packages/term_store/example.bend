import Base
import ./main.bend as S

def shown(r: Result<S.Error,U32>) -> IO(Unit):
  match r:
    case Fail{e}: IO.die(Unit,1,"store failed")
    case Done{x}: IO.print(String.append("term=",U32.show(x)))

def read(p: S.Store<U32> & Result<S.Error,U32>) -> IO(Unit):
  (s,r) = p
  shown(r)

def allocated(p: S.Store<U32> & Result<S.Error,S.Id>) -> IO(Unit):
  (s,r) = p
  match r:
    case Fail{e}: IO.die(Unit,1,"allocation failed")
    case Done{id}: read(S.Store.get(U32,s,id))

def store_ready(r: Result<S.Error,S.Store<U32>>) -> IO(Unit):
  match r:
    case Fail{e}: IO.die(Unit,1,"scope exhausted")
    case Done{s}: allocated(S.Store.alloc(U32,s,73))

def created(p: S.Scopes & Result<S.Error,S.Store<U32>>) -> IO(Unit):
  (scopes,r) = p
  store_ready(r)

def main() -> IO(Unit):
  created(S.Store.new(U32,S.Scopes.new(),2))
