import Base
import ./main.bend as S

# Deliberately linear immutable list model. No production operation calls.
type Arena<-T: Data> is Data:
  Arena{scope: U32, bound: Nat, values: List<&2,T>}

def append(-T: Data,xs: List<&2,T>,x: T) -> List<&2,T>:
  match xs:
    case Nil{}:
      Con{x,Nil{}}
    case Con{y,ys}:
      Con{y,append(T,ys,x)}

def at(-T: Data,xs: List<&2,T>,i: Nat) -> Result<S.Error,T>:
  match xs:
    case Nil{}:
      Fail{S.Bounds{}}
    case Con{x,rest}:
      match i:
        case 0n:
          Done{x}
        case 1n+p:
          at(T,rest,p)

def replace(-T: Data,xs: List<&2,T>,i: Nat,x: T) -> List<&2,T>:
  match xs:
    case Nil{}:
      Nil{}
    case Con{y,rest}:
      match i:
        case 0n:
          Con{x,rest}
        case 1n+p:
          Con{y,replace(T,rest,p,x)}

def count(-T: Data,xs: List<&2,T>) -> Nat:
  match xs:
    case Nil{}:
      0n
    case Con{x,rest}:
      1n+count(T,rest)

def allocate_if(-T: Data,+k: U32,b: Nat,xs: List<&2,T>,x: T,n: Nat,room: Bool) -> Arena<T> & Result<S.Error,S.Id>:
  match room:
    case False{}:
      (Arena{k,b,xs},Fail{S.Limit{}})
    case True{}:
      (Arena{k,b,append(T,xs,x)},Done{S.Id{k,U32.from_nat(n)}})

def allocate(-T: Data,a: Arena<T>,x: T) -> Arena<T> & Result<S.Error,S.Id>:
  match a:
    case Arena{k,+b,+xs}:
      allocate_if(T,k,b,xs,x,count(T,xs),Nat.is_lt(count(T,xs),b))

def read_scoped(-T: Data,xs: List<&2,T>,i: Nat,same: Bool) -> Result<S.Error,T>:
  match same:
    case False{}:
      Fail{S.WrongScope{}}
    case True{}:
      at(T,xs,i)

def read(-T: Data,a: Arena<T>,id: S.Id) -> Result<S.Error,T>:
  match a:
    case Arena{k,b,xs}:
      match id:
        case S.Id{j,i}:
          read_scoped(T,xs,U32.to_nat(i),U32.is_eq(k,j))

def write_bound(-T: Data,k: U32,b: Nat,xs: List<&2,T>,i: Nat,x: T,valid: Bool) -> Arena<T> & Result<S.Error,Unit>:
  match valid:
    case False{}:
      (Arena{k,b,xs},Fail{S.Bounds{}})
    case True{}:
      (Arena{k,b,replace(T,xs,i,x)},Done{Unit{}})

def write_scoped(-T: Data,k: U32,b: Nat,+xs: List<&2,T>,+i: Nat,x: T,same: Bool) -> Arena<T> & Result<S.Error,Unit>:
  match same:
    case False{}:
      (Arena{k,b,xs},Fail{S.WrongScope{}})
    case True{}:
      write_bound(T,k,b,xs,i,x,Nat.is_lt(i,count(T,xs)))

def write(-T: Data,a: Arena<T>,id: S.Id,x: T) -> Arena<T> & Result<S.Error,Unit>:
  match a:
    case Arena{+k,b,xs}:
      match id:
        case S.Id{j,i}:
          write_scoped(T,k,b,xs,U32.to_nat(i),x,U32.is_eq(k,j))

# The model drives from ACTION, while the implementation drives from STATE.
# Each case independently states accepted predecessor and exact successor.
def begin(-T: Data,-E: Data,c: S.Cell<T,E>) -> S.Cell<T,E> & Result<S.Error,Unit>:
  match c:
    case S.Pending{}:
      (S.Evaluating{},Done{Unit{}})
    case S.Evaluating{}:
      (S.Evaluating{},Fail{S.InvalidTransition{}})
    case S.Ready{x}:
      (S.Ready{x},Fail{S.InvalidTransition{}})
    case S.Failed{e}:
      (S.Failed{e},Fail{S.InvalidTransition{}})

def finish(-T: Data,-E: Data,c: S.Cell<T,E>,next: S.Cell<T,E>) -> S.Cell<T,E> & Result<S.Error,Unit>:
  match c:
    case S.Pending{}:
      (S.Pending{},Fail{S.InvalidTransition{}})
    case S.Evaluating{}:
      (next,Done{Unit{}})
    case S.Ready{x}:
      (S.Ready{x},Fail{S.InvalidTransition{}})
    case S.Failed{e}:
      (S.Failed{e},Fail{S.InvalidTransition{}})

def step(-T: Data,-E: Data,a: S.Action<T,E>,c: S.Cell<T,E>) -> S.Cell<T,E> & Result<S.Error,Unit>:
  match a:
    case S.Begin{}:
      begin(T,E,c)
    case S.Succeed{x}:
      finish(T,E,c,S.Ready{x})
    case S.Reject{e}:
      finish(T,E,c,S.Failed{e})
    case S.Cancel{}:
      finish(T,E,c,S.Pending{})
