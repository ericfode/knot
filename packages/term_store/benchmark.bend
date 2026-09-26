import Base
import ./main.bend as S
import ./checks.bend as C

def allocated(+i: U32,ok: Bool,p: S.Store<U32> & Result<S.Error,S.Id>) -> S.Store<U32> & Bool:
  (s,r) = p
  (s,Bool.and(ok,C.alloc_eq(r,Done{S.Id{0,i}})))

def push(+i: U32,p: S.Store<U32> & Bool) -> S.Store<U32> & Bool:
  (s,ok) = p
  allocated(i,ok,S.Store.alloc(U32,s,i))

def fill(n: Nat,+i: U32,p: S.Store<U32> & Bool) -> S.Store<U32> & Bool:
  match n:
    case 0n: p
    case 1n+k: fill(k,U32.add(i,1),push(i,p))

def observed(expected: U32,ok: Bool,p: S.Store<U32> & Result<S.Error,U32>) -> S.Store<U32> & Bool:
  (s,r) = p
  (s,Bool.and(ok,C.value_eq(r,Done{expected})))

def read(+i: U32,p: S.Store<U32> & Bool) -> S.Store<U32> & Bool:
  (s,ok) = p
  observed(i,ok,S.Store.get(U32,s,S.Id{0,i}))

def scan(n: Nat,+i: U32,p: S.Store<U32> & Bool) -> S.Store<U32> & Bool:
  match n:
    case 0n: p
    case 1n+k: scan(k,U32.add(i,1),read(i,p))

def done(p: S.Store<U32> & Bool) -> Bool:
  (s,ok) = p
  ok

def started(+n: Nat,r: Result<S.Error,S.Store<U32>>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: done(scan(n,0,fill(n,0,(s,True{}))))

def created(n: Nat,p: S.Scopes & Result<S.Error,S.Store<U32>>) -> Bool:
  (scopes,r) = p
  started(n,r)

def run(+n: Nat) -> Bool:
  created(n,S.Store.new(U32,S.Scopes.new(),U32.from_nat(n)))

def report(n: Nat,ok: Bool) -> IO(Unit):
  match ok:
    case False{}: IO.die(Unit,1,"benchmark content failure")
    case True{}: IO.print(String.append("PASS n=",Nat.show(n)))

def parsed(r: Maybe<&2,Nat>) -> IO(Unit):
  match r:
    case None{}: IO.die(Unit,2,"expected cell count")
    case Some{+n}: report(n,run(n))

def args(xs: List<String>) -> IO(Unit):
  match xs:
    case Nil{}: IO.die(Unit,2,"expected cell count")
    case Con{x,rest}: parsed(Nat.read(x))

def main() -> IO(Unit):
  do IO<Unit>:
    xs : List<String> <- IO.args()
    args(xs)
