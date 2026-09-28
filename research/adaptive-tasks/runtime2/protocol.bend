import Base

# These lists describe ownership; copying a model snapshot grants no authority.
type Config is Data:
  Config{objects: U32, captures: U32, pending: U32, joins: U32, arity: U32,
    rcLimit: U32, idLimit: U32, attemptLimit: U32, instructionCount: U32}
type Command is Data:
  Command{op: U32, a: U32, b: U32, c: U32, d: U32, e: U32, f: U32, g: U32}
type Object is Data:
  Free{}
  Object{id: U32, kind: U32, rc: U32, tag: U32, children: List<&2,U32>}
type Join is Data:
  Join{attempt: U32, phase: U32, arity: U32, received: U32, completions: U32,
    code: U32, base: U32, count: U32, results: List<&2,U32>}
type Store is Data:
  Store{next: U32, readers: U32, freed: U32, objects: List<&2,Object>,
    captures: List<&2,U32>, pending: List<&2,U32>}
type State is Data:
  State{config: Config, store: Store, joins: List<&2,Join>, status: U32, reply: U32}

def choose(-A: Type, test: Bool, yes: Unit -> A, no: Unit -> A) -> A:
  match test:
    case True{}: yes(Unit{})
    case False{}: no(Unit{})

def bind(-A: Data, -B: Data, result: Result<U32,A>, next: A -> Result<U32,B>) -> Result<U32,B>:
  match result:
    case Fail{e}: Fail{e}
    case Done{x}: next(x)

def repeat(-A: Data, n: Nat, +value: A) -> List<&2,A>:
  match n:
    case 0n: Nil{}
    case 1n+n: Con{value,repeat(A,n,value)}

def length(-A: Data, xs: List<&2,A>) -> U32:
  match xs:
    case Nil{}: 0
    case Con{h,t}: U32.add(1,length(A,t))

def at(-A: Data, xs: List<&2,A>, +index: U32, +fallback: A) -> A:
  match xs:
    case Nil{}: fallback
    case Con{+h,+t}: choose(A,U32.is_eq(index,0),u => h,u => at(A,t,U32.sub(index,1),fallback))

def put(-A: Data, xs: List<&2,A>, +index: U32, +value: A) -> List<&2,A>:
  match xs:
    case Nil{}: Nil{}
    case Con{+h,+t}:
      choose(List<&2,A>,U32.is_eq(index,0),u => Con{value,t},u => Con{h,put(A,t,U32.sub(index,1),value)})

def append(-A: Data, xs: List<&2,A>, ys: List<&2,A>) -> List<&2,A>:
  match xs:
    case Nil{}: ys
    case Con{h,t}: Con{h,append(A,t,ys)}

def slice(xs: List<&2,U32>, +first: U32, +count: U32) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case Con{+h,+t}:
      choose(List<&2,U32>,U32.is_eq(count,0),u => Nil{},u =>
        choose(List<&2,U32>,U32.is_eq(first,0),u => Con{h,slice(t,0,U32.sub(count,1))},u => slice(t,U32.sub(first,1),count)))

def write(xs: List<&2,U32>, +first: U32, values: List<&2,U32>) -> List<&2,U32>:
  match xs values:
    case Nil{} _: Nil{}
    case Con{h,t} Nil{}: Con{h,t}
    case Con{+h,+t} Con{+v,+vs}:
      choose(List<&2,U32>,U32.is_eq(first,0),u => Con{v,write(t,0,vs)},u => Con{h,write(t,U32.sub(first,1),Con{v,vs})})

def clear(xs: List<&2,U32>, +first: U32, +count: U32) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case Con{+h,+t}:
      choose(List<&2,U32>,U32.is_eq(count,0),u => Con{h,t},u =>
        choose(List<&2,U32>,U32.is_eq(first,0),u => Con{0,clear(t,0,U32.sub(count,1))},u => Con{h,clear(t,U32.sub(first,1),count)}))

def range(+first: U32, +count: U32, +limit: U32) -> Bool:
  choose(Bool,U32.is_le(first,limit),u => U32.is_le(count,U32.sub(limit,first)),u => False{})

def inside(+index: U32, +first: U32, count: U32) -> Bool:
  choose(Bool,U32.is_ge(index,first),u => U32.is_lt(U32.sub(index,first),count),u => False{})

def vacant(xs: List<&2,U32>) -> Bool:
  match xs:
    case Nil{}: True{}
    case Con{h,t}: Bool.and(U32.is_eq(h,0),vacant(t))

def occupied(xs: List<&2,U32>) -> Bool:
  match xs:
    case Nil{}: True{}
    case Con{h,t}: Bool.and(U32.is_ne(h,0),occupied(t))

def live(xs: List<&2,U32>) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case Con{+h,+t}: choose(List<&2,U32>,U32.is_eq(h,0),u => live(t),u => Con{h,live(t)})

def find(xs: List<&2,Object>, +id: U32) -> Object:
  match xs:
    case Nil{}: Free{}
    case Con{Free{},t}: find(t,id)
    case Con{Object{+key,+kind,+rc,+tag,+children},+t}:
      choose(Object,U32.is_eq(key,id),u => Object{key,kind,rc,tag,children},u => find(t,id))

def replace(xs: List<&2,Object>, +id: U32, +value: Object) -> List<&2,Object>:
  match xs:
    case Nil{}: Nil{}
    case Con{Free{},t}: Con{Free{},replace(t,id,value)}
    case Con{Object{+key,+kind,+rc,+tag,+children},+t}:
      choose(List<&2,Object>,U32.is_eq(key,id),u => Con{value,t},u => Con{Object{key,kind,rc,tag,children},replace(t,id,value)})

def room(xs: List<&2,Object>) -> Bool:
  match xs:
    case Nil{}: False{}
    case Con{Free{},t}: True{}
    case Con{Object{i,k,r,v,cs},t}: room(t)

def insert(xs: List<&2,Object>, value: Object) -> List<&2,Object>:
  match xs:
    case Nil{}: Nil{}
    case Con{Free{},t}: Con{value,t}
    case Con{h,t}: Con{h,insert(t,value)}

def empty_join() -> Join:
  Join{0,0,0,0,0,0,0,0,Nil{}}

def result(state: State, status: U32, reply: U32) -> State:
  match state:
    case State{config,store,joins,old,value}: State{config,store,joins,status,reply}

def status(state: State) -> U32:
  match state:
    case State{config,store,joins,status,reply}: status

def stored(state: State, store: Store) -> State:
  match state:
    case State{config,old,joins,status,reply}: State{config,store,joins,0,0}

def updated(state: State, store: Store, joins: List<&2,Join>, status: U32, reply: U32) -> State:
  match state:
    case State{config,old,oldjoins,oldstatus,oldreply}: State{config,store,joins,status,reply}

def initial(+config: Config) -> State:
  match config:
    case Config{objects,captures,pending,joins,arity,rcLimit,idLimit,attemptLimit,instructionCount}:
      State{config,Store{1,0,0,repeat(Object,U32.to_nat(objects),Free{}),repeat(U32,U32.to_nat(captures),0),Nil{}},
        repeat(Join,U32.to_nat(joins),empty_join()),0,0}
