import Base
import ../owned-store/store.bend as S
import ../owned-store/protocol.bend as P
import ../owned-store/model.bend as M

type Reply is Data:
  Reply{status: U32, slot: U32, generation: U32, value: U32}

def status(error: S.Error) -> U32:
  match error:
    case S.Limit{}: 1
    case S.Full{}: 2
    case S.Bounds{}: 3
    case S.WrongArena{}: 4
    case S.Stale{}: 5
    case S.Vacant{}: 6
    case S.Occupied{}: 7
    case S.Retired{}: 8

def incoming(value: Maybe<&2,U32>) -> U32:
  match value:
    case None{}: 0
    case Some{x}: x

def transferred(command: P.Command, value: U32) -> Reply:
  match command:
    case P.Extract{S.Locator{arena,slot,generation}}: Reply{0,slot,generation,value}
    case P.Dispose{S.Locator{arena,slot,generation}}: Reply{0,slot,generation,value}
    case other: Reply{11,4294967295,4294967295,value}

def reply(event: P.Observation, command: P.Command) -> Reply:
  match event:
    case P.Allocated{S.Locator{arena,slot,generation}}: Reply{0,slot,generation,0}
    case P.Rejected{error,value}: Reply{status(error),4294967295,4294967295,incoming(value)}
    case P.Extracted{value}: transferred(command,value)
    case P.Disposed{value}: transferred(command,value)

def head(xs: List<&2,U32>) -> U32:
  match xs:
    case Nil{}: 4294967295
    case Con{x,tail}: x

def link(free: List<&2,U32>, +index: U32) -> U32:
  match free:
    case Nil{}: 4294967295
    case Con{current,+tail}:
      Bool.pick(U32,U32.is_eq(current,index),head(tail),link(tail,index))

def cell(value: P.Cell, index: U32, ceiling: U32, free: List<&2,U32>) -> List<&2,U32>:
  match value:
    case P.Hole{generation}: [0,generation,0,link(free,index)]
    case P.Item{generation,serial}: [1,generation,serial,4294967295]
    case P.Tomb{}: [2,ceiling,0,4294967295]

def cells(values: List<&2,P.Cell>, +index: U32, +ceiling: U32, +free: List<&2,U32>) -> List<&2,U32>:
  match values:
    case Nil{}: Nil{}
    case Con{value,tail}:
      List.append(&2,U32,cell(value,index,ceiling,free),cells(tail,U32.add(index,1),ceiling,free))

def words(state: P.Snapshot, result: Reply, disposed: U32) -> List<&2,U32>:
  match state result:
    case P.Snapshot{arena,capacity,+ceiling,+free,values} Reply{status,slot,generation,value}:
      List.append(&2,U32,[arena,capacity,ceiling,head(free),slot,generation,value,disposed],cells(values,0,ceiling,free))

def disposals(event: P.Observation, +count: U32) -> U32:
  match event:
    case P.Disposed{value}: U32.add(count,1)
    case other: count

def name(command: P.Command) -> String:
  match command:
    case P.Insert{index,value}: "put"
    case P.Reserve{value}: "alloc"
    case P.Extract{key}: "take"
    case P.Dispose{key}: "release"

def locator(key: S.Locator) -> List<&2,U32>:
  match key:
    case S.Locator{arena,index,generation}: [arena,index,generation]

def args(command: P.Command) -> List<&2,U32>:
  match command:
    case P.Insert{index,value}: [index,value]
    case P.Reserve{value}: [value]
    case P.Extract{key}: locator(key)
    case P.Dispose{key}: locator(key)

def row(id: U32, operation: String, arguments: List<&2,U32>, result: Reply, words: List<&2,U32>) -> String:
  match result:
    case Reply{status,slot,generation,value}:
      String.join([U32.show(id),operation,List.show(~&2,~U32,~U32.show,arguments),U32.show(status),List.show(~&2,~U32,~U32.show,words)],"|")

def observed(id: U32, +command: P.Command, count: U32, pair: P.Snapshot & P.Observation, next: P.Snapshot -> U32 -> IO(Unit)) -> IO(Unit):
  (+state,+event) = pair
  +result : Reply = reply(event,command)
  +total = disposals(event,count)
  do IO<Unit>:
    IO.print(row(id,name(command),args(command),result,words(state,result,total)))
    next(state,total)

def run(commands: List<&2,P.Command>, state: P.Snapshot, count: U32, +id: U32) -> IO(Unit):
  match commands:
    case Nil{}: IO.pure(Unit,Unit{})
    case Con{+command,tail}:
      observed(id,command,count,M.step(command,state),state => count => run(tail,state,count,id))

def start(valid: Bool, test: P.Case) -> IO(Unit):
  match valid test:
    case False{} P.Case{id,arena,capacity,ceiling,commands}:
      IO.print(row(id,"init",[arena,capacity,ceiling],Reply{1,4294967295,4294967295,0},Nil{}))
    case True{} P.Case{+id,+arena,+capacity,+ceiling,commands}:
      +state : P.Snapshot = P.Snapshot{arena,capacity,ceiling,M.positions(U32.to_nat(capacity),0),M.blank(U32.to_nat(capacity))}
      +result : Reply = Reply{0,4294967295,4294967295,0}
      do IO<Unit>:
        IO.print(row(id,"init",[arena,capacity,ceiling],result,words(state,result,0)))
        run(commands,state,0,id)

def test(test: P.Case) -> IO(Unit):
  match test:
    case P.Case{id,arena,+capacity,ceiling,commands}:
      start(U32.is_le(capacity,4096),P.Case{id,arena,capacity,ceiling,commands})

def tests(cases: List<&2,P.Case>) -> IO(Unit):
  match cases:
    case Nil{}: IO.pure(Unit,Unit{})
    case Con{current,tail}:
      do IO<Unit>:
        test(current)
        tests(tail)

def boundary(+id: U32, +generation: U32) -> IO(Unit):
  +initial : P.Snapshot = P.Snapshot{41,1,4294967295,[0],[P.Hole{0}]}
  +seed : P.Snapshot = P.Snapshot{41,1,4294967295,Nil{},[P.Item{generation,7}]}
  +result : Reply = Reply{0,4294967295,4294967295,0}
  do IO<Unit>:
    IO.print(row(id,"init",[41,1,4294967295],result,words(initial,result,0)))
    IO.print(row(id,"install",Nil{},result,words(seed,result,0)))
    run([P.Extract{S.Locator{41,0,generation}},P.Reserve{9},P.Dispose{S.Locator{41,0,4294967295}},P.Reserve{11}],seed,0,id)
