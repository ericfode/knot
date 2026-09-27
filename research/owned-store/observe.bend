import Base
import ./store.bend as S
import ./protocol.bend as P

type Payload is Type:
  Owned{serial: U32}

def serial(value: Payload) -> U32:
  match value:
    case Owned{id}: id

def cell(c: S.Cell<Payload>) -> P.Cell:
  match c:
    case S.Free{generation}: P.Hole{generation}
    case S.Live{generation,value}: P.Item{generation,serial(value)}
    case S.Dead{}: P.Tomb{}

def cells(xs: List<S.Cell<Payload>>) -> List<&2,P.Cell>:
  match xs:
    case Nil{}: Nil{}
    case Con{head,tail}: Con{cell(head),cells(tail)}

def snapshot(store: S.Store<Payload>) -> P.Snapshot:
  match store:
    case S.Store{arena,+capacity,ceiling,free,backing}:
      P.Snapshot{arena,capacity,ceiling,free,List.take(&2,P.Cell,cells(Array.to_list(~S.Cell<Payload>,backing)),U32.to_nat(capacity))}

def placed(result: S.Put<Payload>) -> S.Store<Payload> & P.Observation:
  match result:
    case S.Placed{store,key}: (store,P.Allocated{key})
    case S.PutFailed{store,error,value}: (store,P.Rejected{error,Some{serial(value)}})

def taken(result: S.Take<Payload>) -> S.Store<Payload> & P.Observation:
  match result:
    case S.Taken{store,value}: (store,P.Extracted{serial(value)})
    case S.TakeFailed{store,error}: (store,P.Rejected{error,None{}})

def disposed(result: Result<S.Error,U32>) -> P.Observation:
  match result:
    case Done{value}: P.Disposed{value}
    case Fail{error}: P.Rejected{error,None{}}

def released(pair: S.Store<Payload> & Result<S.Error,U32>) -> S.Store<Payload> & P.Observation:
  (store,result) = pair
  (store,disposed(result))

def step(command: P.Command, store: S.Store<Payload>) -> S.Store<Payload> & P.Observation:
  match command:
    case P.Insert{index,value}: placed(S.put(Payload,store,index,Owned{value}))
    case P.Reserve{value}: placed(S.alloc(Payload,store,Owned{value}))
    case P.Extract{key}: taken(S.take(Payload,store,key))
    case P.Dispose{key}: released(S.release(Payload,U32,store,key,serial))

def continue(result: S.Store<Payload> & P.Observation, next: S.Store<Payload> -> P.Observation -> String) -> String:
  (store,event) = result
  next(store,event)

def run(commands: List<&2,P.Command>, store: S.Store<Payload>, events: List<&2,P.Observation>) -> String:
  match commands:
    case Nil{}: P.observation(List.reverse(&2,P.Observation,events),snapshot(store))
    case Con{command,tail}: continue(step(command,store),store => event => run(tail,store,Con{event,events}))

def start(result: Result<&2,&1,S.Error,S.Store<Payload>>, commands: List<&2,P.Command>) -> String:
  match result:
    case Fail{e}: String.append("new:",P.error(e))
    case Done{store}: run(commands,store,Nil{})
