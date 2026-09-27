import Base
import ./protocol.bend as P
import ./store.bend as S

# The reference traverses lists and copies Data. It calls no store operation.
def blank(n: Nat) -> List<&2,P.Cell>:
  match n:
    case 0n: Nil{}
    case 1n+tail: Con{P.Hole{0},blank(tail)}

def positions(n: Nat, +index: U32) -> List<&2,U32>:
  match n:
    case 0n: Nil{}
    case 1n+tail: Con{index,positions(tail,U32.add(index,1))}

def find(index: Nat, cells: List<&2,P.Cell>) -> Maybe<&2,P.Cell>:
  match index cells:
    case 0n Nil{}: None{}
    case 0n Con{head,tail}: Some{head}
    case 1n+n Nil{}: None{}
    case 1n+n Con{head,tail}: find(n,tail)

def write(index: Nat, cells: List<&2,P.Cell>, +value: P.Cell) -> List<&2,P.Cell>:
  match index cells:
    case 0n Nil{}: Nil{}
    case 0n Con{head,tail}: Con{value,tail}
    case 1n+n Nil{}: Nil{}
    case 1n+n Con{head,tail}: Con{head,write(n,tail,value)}

def exclude(free: List<&2,U32>, +index: U32) -> List<&2,U32>:
  match free:
    case Nil{}: Nil{}
    case Con{+head,tail}:
      +rest = exclude(tail,index)
      Bool.pick(List<&2,U32>,U32.is_eq(head,index),rest,Con{head,rest})

def insert_cell(cell: Maybe<&2,P.Cell>, +state: P.Snapshot, +index: U32, +value: U32) -> P.Snapshot & P.Observation:
  match cell state:
    case None{} _: (state,P.Rejected{S.Bounds{},Some{value}})
    case Some{P.Tomb{}} _: (state,P.Rejected{S.Retired{},Some{value}})
    case Some{P.Item{generation,old}} _: (state,P.Rejected{S.Occupied{},Some{value}})
    case Some{P.Hole{+generation}} P.Snapshot{+arena,capacity,ceiling,free,cells}:
      (P.Snapshot{arena,capacity,ceiling,exclude(free,index),write(U32.to_nat(index),cells,P.Item{generation,value})},
        P.Allocated{S.Locator{arena,index,generation}})

def insert_bound(valid: Bool, +state: P.Snapshot, +index: U32, value: U32) -> P.Snapshot & P.Observation:
  match valid state:
    case False{} _: (state,P.Rejected{S.Bounds{},Some{value}})
    case True{} P.Snapshot{arena,capacity,ceiling,free,cells}:
      insert_cell(find(U32.to_nat(index),cells),state,index,value)

def insert(+state: P.Snapshot, +index: U32, value: U32) -> P.Snapshot & P.Observation:
  match state:
    case P.Snapshot{arena,capacity,ceiling,free,cells}: insert_bound(U32.is_lt(index,capacity),state,index,value)

def reserve(+state: P.Snapshot, value: U32) -> P.Snapshot & P.Observation:
  match state:
    case P.Snapshot{arena,capacity,ceiling,Nil{},cells}: (state,P.Rejected{S.Full{},Some{value}})
    case P.Snapshot{arena,capacity,ceiling,Con{index,tail},cells}: insert(state,index,value)

def emit(drop: Bool, +value: U32) -> P.Observation:
  Bool.pick(P.Observation,drop,P.Disposed{value},P.Extracted{value})

def advance(reusable: Bool, state: P.Snapshot, +index: U32, generation: U32, drop: Bool, value: U32) -> P.Snapshot & P.Observation:
  match reusable state:
    case True{} P.Snapshot{arena,capacity,ceiling,free,cells}:
      (P.Snapshot{arena,capacity,ceiling,Con{index,free},write(U32.to_nat(index),cells,P.Hole{U32.add(generation,1)})},emit(drop,value))
    case False{} P.Snapshot{arena,capacity,ceiling,free,cells}:
      (P.Snapshot{arena,capacity,ceiling,free,write(U32.to_nat(index),cells,P.Tomb{})},emit(drop,value))

def take_live(valid: Bool, +state: P.Snapshot, index: U32, +generation: U32, drop: Bool, value: U32) -> P.Snapshot & P.Observation:
  match valid state:
    case False{} _: (state,P.Rejected{S.Stale{},None{}})
    case True{} P.Snapshot{arena,capacity,ceiling,free,cells}:
      advance(U32.is_lt(generation,ceiling),state,index,generation,drop,value)

def take_cell(cell: Maybe<&2,P.Cell>, +state: P.Snapshot, index: U32, generation: U32, drop: Bool) -> P.Snapshot & P.Observation:
  match cell:
    case None{}: (state,P.Rejected{S.Bounds{},None{}})
    case Some{P.Tomb{}}: (state,P.Rejected{S.Retired{},None{}})
    case Some{P.Hole{current}}:
      (state,P.Rejected{Bool.pick(S.Error,U32.is_eq(current,generation),S.Vacant{},S.Stale{}),None{}})
    case Some{P.Item{+current,value}}: take_live(U32.is_eq(current,generation),state,index,current,drop,value)

def take_bound(valid: Bool, +state: P.Snapshot, +index: U32, generation: U32, drop: Bool) -> P.Snapshot & P.Observation:
  match valid state:
    case False{} _: (state,P.Rejected{S.Bounds{},None{}})
    case True{} P.Snapshot{arena,capacity,ceiling,free,cells}:
      take_cell(find(U32.to_nat(index),cells),state,index,generation,drop)

def take_realm(valid: Bool, +state: P.Snapshot, +index: U32, generation: U32, drop: Bool) -> P.Snapshot & P.Observation:
  match valid state:
    case False{} _: (state,P.Rejected{S.WrongArena{},None{}})
    case True{} P.Snapshot{arena,capacity,ceiling,free,cells}:
      take_bound(U32.is_lt(index,capacity),state,index,generation,drop)

def take(+state: P.Snapshot, key: S.Locator, drop: Bool) -> P.Snapshot & P.Observation:
  match state key:
    case P.Snapshot{arena,capacity,ceiling,free,cells} S.Locator{realm,index,generation}:
      take_realm(U32.is_eq(arena,realm),state,index,generation,drop)

def step(command: P.Command, state: P.Snapshot) -> P.Snapshot & P.Observation:
  match command:
    case P.Insert{index,value}: insert(state,index,value)
    case P.Reserve{value}: reserve(state,value)
    case P.Extract{key}: take(state,key,False{})
    case P.Dispose{key}: take(state,key,True{})

def continue(result: P.Snapshot & P.Observation, next: P.Snapshot -> P.Observation -> String) -> String:
  (state,event) = result
  next(state,event)

def run(commands: List<&2,P.Command>, state: P.Snapshot, events: List<&2,P.Observation>) -> String:
  match commands:
    case Nil{}: P.observation(List.reverse(&2,P.Observation,events),state)
    case Con{command,tail}: continue(step(command,state),state => event => run(tail,state,Con{event,events}))

def bounded(valid: Bool, arena: U32, +capacity: U32, ceiling: U32, commands: List<&2,P.Command>) -> String:
  match valid:
    case False{}: "new:limit"
    case True{}:
      run(commands,P.Snapshot{arena,capacity,ceiling,positions(U32.to_nat(capacity),0),blank(U32.to_nat(capacity))},Nil{})

def start(arena: U32, +capacity: U32, ceiling: U32, commands: List<&2,P.Command>) -> String:
  bounded(U32.is_le(capacity,4096),arena,capacity,ceiling,commands)
