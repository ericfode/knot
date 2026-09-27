import Base
import ./store.bend as S

# Test observations contain serials, never an owned payload.
type Cell is Data:
  Hole{generation: U32}
  Item{generation: U32, serial: U32}
  Tomb{}
type Command is Data:
  Insert{index: U32, serial: U32}
  Reserve{serial: U32}
  Extract{key: S.Locator}
  Dispose{key: S.Locator}
type Observation is Data:
  Allocated{key: S.Locator}
  Rejected{error: S.Error, incoming: Maybe<&2,U32>}
  Extracted{serial: U32}
  Disposed{serial: U32}
type Snapshot is Data:
  Snapshot{arena: U32, capacity: U32, ceiling: U32, free: List<&2,U32>, cells: List<&2,Cell>}
type Case is Data:
  Case{id: U32, arena: U32, capacity: U32, ceiling: U32, commands: List<&2,Command>}

def error(e: S.Error) -> String:
  match e:
    case S.Limit{}: "limit"
    case S.Full{}: "full"
    case S.Bounds{}: "bounds"
    case S.WrongArena{}: "arena"
    case S.Stale{}: "stale"
    case S.Vacant{}: "vacant"
    case S.Occupied{}: "occupied"
    case S.Retired{}: "retired"

def locator(key: S.Locator) -> String:
  match key:
    case S.Locator{arena,slot,generation}: String.join([U32.show(arena),U32.show(slot),U32.show(generation)],",")

def maybe(value: Maybe<&2,U32>) -> String:
  match value:
    case None{}: "-"
    case Some{x}: U32.show(x)

def event(e: Observation) -> String:
  match e:
    case Allocated{key}: String.append("alloc:",locator(key))
    case Rejected{reason,incoming}: String.join(["fail",error(reason),maybe(incoming)],":")
    case Extracted{serial}: String.append("take:",U32.show(serial))
    case Disposed{serial}: String.append("drop:",U32.show(serial))

def cell(c: Cell) -> String:
  match c:
    case Hole{generation}: String.append("free:",U32.show(generation))
    case Item{generation,serial}: String.join(["live",U32.show(generation),U32.show(serial)],":")
    case Tomb{}: "retired"

def snapshot(s: Snapshot) -> String:
  match s:
    case Snapshot{arena,capacity,ceiling,free,cells}:
      String.join([U32.show(arena),U32.show(capacity),U32.show(ceiling),
        List.show(~&2,~U32,~U32.show,free),List.show(~&2,~Cell,~cell,cells)],";")

def observation(events: List<&2,Observation>, s: Snapshot) -> String:
  String.concat([List.show(~&2,~Observation,~event,events),"/",snapshot(s)])
