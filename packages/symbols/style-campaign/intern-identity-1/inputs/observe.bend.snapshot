import Base
import ./main.bend as S
import ./protocol.bend as P

def error_reply(e: S.Error) -> P.Reply:
  match e:
    case S.InvalidId{}: P.Invalid{}
    case S.Exhausted{}: P.Full{}

def intern_reply(pair: S.Table & Result<S.Error,U32>) -> S.Table & P.Reply:
  (t,r) = pair
  match r:
    case Done{i}: (t,P.Id{i})
    case Fail{e}: (t,error_reply(e))

def resolve_reply(pair: S.Table & Result<S.Error,String>) -> S.Table & P.Reply:
  (t,r) = pair
  match r:
    case Done{name}: (t,P.Name{name})
    case Fail{e}: (t,error_reply(e))

def find_reply(pair: S.Table & Maybe<&2,U32>) -> S.Table & P.Reply:
  (t,r) = pair
  match r:
    case Some{i}: (t,P.Id{i})
    case None{}: (t,P.Missing{})

def number_reply(pair: S.Table & U32) -> S.Table & P.Reply:
  (t,n) = pair
  (t,P.Number{n})

def step(command: P.Command, t: S.Table) -> S.Table & P.Reply:
  match command:
    case P.Intern{name}: intern_reply(S.Table.intern(t,name))
    case P.Find{name}: find_reply(S.Table.find(t,name))
    case P.Resolve{i}: resolve_reply(S.Table.resolve(t,i))
    case P.Length{}: number_reply(S.Table.length(t))
    case P.Limit{}: number_reply(S.Table.limit(t))

def collect_join(name: String, pair: S.Table & List<&2,String>) -> S.Table & List<&2,String>:
  (t,xs) = pair
  (t,Con{name,xs})

def collect_next(next: S.Table -> S.Table & List<&2,String>, pair: S.Table & Result<S.Error,String>) -> S.Table & List<&2,String>:
  (t,r) = pair
  match r:
    case Fail{e}: (t,Nil{})
    case Done{name}: collect_join(name,next(t))

def collect(count: Nat, +index: U32, t: S.Table) -> S.Table & List<&2,String>:
  match count:
    case 0n: (t,Nil{})
    case 1n+p: collect_next(collect(p,U32.add(index,1)),S.Table.resolve(t,index))

def observed(r: P.Reply, n: U32, limit: U32, pair: S.Table & List<&2,String>) -> S.Table & P.Observation:
  (t,xs) = pair
  (t,P.Observed{r,n,limit,xs})

def with_limit(r: P.Reply, +n: U32, pair: S.Table & U32) -> S.Table & P.Observation:
  (t,limit) = pair
  observed(r,n,limit,collect(U32.to_nat(n),0,t))

def with_length(r: P.Reply, pair: S.Table & U32) -> S.Table & P.Observation:
  (t,n) = pair
  with_limit(r,n,S.Table.limit(t))

def snapshot(pair: S.Table & P.Reply) -> S.Table & P.Observation:
  (t,r) = pair
  with_length(r,S.Table.length(t))

def trace_next(next: S.Table -> List<&2,P.Observation>, pair: S.Table & P.Observation) -> List<&2,P.Observation>:
  (t,r) = pair
  Con{r,next(t)}

def trace(commands: List<&2,P.Command>, t: S.Table) -> List<&2,P.Observation>:
  match commands:
    case Nil{}: Nil{}
    case Con{c,cs}: trace_next(trace(cs),snapshot(step(c,t)))

def run(commands: List<&2,P.Command>, limit: U32) -> List<&2,P.Observation>:
  trace(commands,S.Table.bounded(limit))
