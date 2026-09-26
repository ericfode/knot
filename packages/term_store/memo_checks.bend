import Base
import ./main.bend as S
import ./model.bend as M
import ./checks.bend as C

type Seen is Data:
  Added{id: S.Id}
  Changed{}
  Value{x: U32}
  Rejected{e: U32}
  Fault{e: U32}

type Op is Data:
  Add{}
  Apply{id: S.Id,action: S.Action<U32,U32>}
  Observe{id: S.Id}

def allocated(r: Result<S.Error,S.Id>) -> Seen:
  match r:
    case Fail{e}: Fault{C.error_code(e)}
    case Done{id}: Added{id}

def changed(r: Result<S.Error,Unit>) -> Seen:
  match r:
    case Fail{e}: Fault{C.error_code(e)}
    case Done{u}: Changed{}

def inner(r: Result<U32,U32>) -> Seen:
  match r:
    case Fail{e}: Rejected{e}
    case Done{x}: Value{x}

def completed(r: Result<S.Error,Result<U32,U32>>) -> Seen:
  match r:
    case Fail{e}: Fault{C.error_code(e)}
    case Done{x}: inner(x)

# Independent observation table, never calls Cell.result.
def observe_cell(r: Result<S.Error,S.Cell<U32,U32>>) -> Seen:
  match r:
    case Fail{e}: Fault{C.error_code(e)}
    case Done{c}:
      match c:
        case S.Pending{}: Fault{6}
        case S.Evaluating{}: Fault{6}
        case S.Ready{x}: Value{x}
        case S.Failed{e}: Rejected{e}

def seen_eq(a: Seen,b: Seen) -> Bool:
  match a:
    case Added{x}:
      match b:
        case Added{y}: C.id_eq(x,y)
        case Changed{}: False{}
        case Value{y}: False{}
        case Rejected{e}: False{}
        case Fault{e}: False{}
    case Changed{}:
      match b:
        case Added{y}: False{}
        case Changed{}: True{}
        case Value{y}: False{}
        case Rejected{e}: False{}
        case Fault{e}: False{}
    case Value{x}:
      match b:
        case Added{y}: False{}
        case Changed{}: False{}
        case Value{y}: U32.is_eq(x,y)
        case Rejected{e}: False{}
        case Fault{e}: False{}
    case Rejected{x}:
      match b:
        case Added{y}: False{}
        case Changed{}: False{}
        case Value{y}: False{}
        case Rejected{e}: U32.is_eq(x,e)
        case Fault{e}: False{}
    case Fault{x}:
      match b:
        case Added{y}: False{}
        case Changed{}: False{}
        case Value{y}: False{}
        case Rejected{e}: False{}
        case Fault{e}: U32.is_eq(x,e)

def cell_eq(a: S.Cell<U32,U32>,b: S.Cell<U32,U32>) -> Bool:
  match a:
    case S.Pending{}:
      match b:
        case S.Pending{}: True{}
        case S.Evaluating{}: False{}
        case S.Ready{x}: False{}
        case S.Failed{e}: False{}
    case S.Evaluating{}:
      match b:
        case S.Pending{}: False{}
        case S.Evaluating{}: True{}
        case S.Ready{x}: False{}
        case S.Failed{e}: False{}
    case S.Ready{x}:
      match b:
        case S.Pending{}: False{}
        case S.Evaluating{}: False{}
        case S.Ready{y}: U32.is_eq(x,y)
        case S.Failed{e}: False{}
    case S.Failed{x}:
      match b:
        case S.Pending{}: False{}
        case S.Evaluating{}: False{}
        case S.Ready{y}: False{}
        case S.Failed{e}: U32.is_eq(x,e)

def cells_eq(a: Result<S.Error,S.Cell<U32,U32>>,b: Result<S.Error,S.Cell<U32,U32>>) -> Bool:
  match a:
    case Fail{e}:
      match b:
        case Fail{f}: C.error_eq(e,f)
        case Done{c}: False{}
    case Done{c}:
      match b:
        case Fail{e}: False{}
        case Done{d}: cell_eq(c,d)

def actual_add(p: S.Memo<U32,U32> & Result<S.Error,S.Id>) -> S.Memo<U32,U32> & Seen:
  (m,r) = p
  (m,allocated(r))

def actual_change(p: S.Memo<U32,U32> & Result<S.Error,Unit>) -> S.Memo<U32,U32> & Seen:
  (m,r) = p
  (m,changed(r))

def actual_observe(p: S.Memo<U32,U32> & Result<S.Error,Result<U32,U32>>) -> S.Memo<U32,U32> & Seen:
  (m,r) = p
  (m,completed(r))

def actual(m: S.Memo<U32,U32>,op: Op) -> S.Memo<U32,U32> & Seen:
  match op:
    case Add{}: actual_add(S.Memo.alloc(U32,U32,m))
    case Observe{id}: actual_observe(S.Memo.result(U32,U32,m,id))
    case Apply{id,a}:
      match a:
        case S.Begin{}: actual_change(S.Memo.begin(U32,U32,m,id))
        case S.Succeed{x}: actual_change(S.Memo.succeed(U32,U32,m,id,x))
        case S.Reject{e}: actual_change(S.Memo.fail(U32,U32,m,id,e))
        case S.Cancel{}: actual_change(S.Memo.cancel(U32,U32,m,id))

def model_add(p: M.Arena<S.Cell<U32,U32>> & Result<S.Error,S.Id>) -> M.Arena<S.Cell<U32,U32>> & Seen:
  (a,r) = p
  (a,allocated(r))

def model_write(p: M.Arena<S.Cell<U32,U32>> & Result<S.Error,Unit>) -> M.Arena<S.Cell<U32,U32>> & Seen:
  (a,r) = p
  (a,changed(r))

def model_commit(a: M.Arena<S.Cell<U32,U32>>,id: S.Id,c: S.Cell<U32,U32>,r: Result<S.Error,Unit>) -> M.Arena<S.Cell<U32,U32>> & Seen:
  match r:
    case Fail{e}: (a,Fault{C.error_code(e)})
    case Done{u}: model_write(M.write(S.Cell<U32,U32>,a,id,c))

def model_step(a: M.Arena<S.Cell<U32,U32>>,id: S.Id,p: S.Cell<U32,U32> & Result<S.Error,Unit>) -> M.Arena<S.Cell<U32,U32>> & Seen:
  (c,r) = p
  model_commit(a,id,c,r)

def model_found(a: M.Arena<S.Cell<U32,U32>>,id: S.Id,action: S.Action<U32,U32>,r: Result<S.Error,S.Cell<U32,U32>>) -> M.Arena<S.Cell<U32,U32>> & Seen:
  match r:
    case Fail{e}: (a,Fault{C.error_code(e)})
    case Done{c}: model_step(a,id,M.step(U32,U32,action,c))

def model(+a: M.Arena<S.Cell<U32,U32>>,op: Op) -> M.Arena<S.Cell<U32,U32>> & Seen:
  match op:
    case Add{}: model_add(M.allocate(S.Cell<U32,U32>,a,S.Pending{}))
    case Observe{id}: (a,observe_cell(M.read(S.Cell<U32,U32>,a,id)))
    case Apply{+id,action}: model_found(a,id,action,M.read(S.Cell<U32,U32>,a,id))

def inspected(expected: Result<S.Error,S.Cell<U32,U32>>,ok: Bool,p: S.Memo<U32,U32> & Result<S.Error,S.Cell<U32,U32>>) -> S.Memo<U32,U32> & Bool:
  (m,r) = p
  (m,Bool.and(ok,cells_eq(expected,r)))

def inspect_one(a: M.Arena<S.Cell<U32,U32>>,+id: S.Id,p: S.Memo<U32,U32> & Bool) -> S.Memo<U32,U32> & Bool:
  (m,ok) = p
  inspected(M.read(S.Cell<U32,U32>,a,id),ok,S.Memo.inspect(U32,U32,m,id))

def inspect_all(left: Nat,+i: U32,+scope: U32,+a: M.Arena<S.Cell<U32,U32>>,p: S.Memo<U32,U32> & Bool) -> S.Memo<U32,U32> & Bool:
  match left:
    case 0n: p
    case 1n+n: inspect_all(n,U32.add(i,1),scope,a,inspect_one(a,S.Id{scope,i},p))

def restored(a: M.Arena<S.Cell<U32,U32>>,p: S.Memo<U32,U32> & Bool) -> S.Memo<U32,U32> & (M.Arena<S.Cell<U32,U32>> & Bool):
  (m,ok) = p
  (m,(a,ok))

def checked(+a: M.Arena<S.Cell<U32,U32>>,m: S.Memo<U32,U32>,ok: Bool) -> S.Memo<U32,U32> & (M.Arena<S.Cell<U32,U32>> & Bool):
  match a:
    case M.Arena{+scope,+bound,+xs}:
      restored(M.Arena{scope,bound,xs},inspect_all(1n+M.count(S.Cell<U32,U32>,xs),0,scope,M.Arena{scope,bound,xs},(m,ok)))

def compared(ok: Bool,q: M.Arena<S.Cell<U32,U32>> & Seen,p: S.Memo<U32,U32> & Seen) -> S.Memo<U32,U32> & (M.Arena<S.Cell<U32,U32>> & Bool):
  (a,expected) = q
  (m,got) = p
  checked(a,m,Bool.and(ok,seen_eq(expected,got)))

def advance(+op: Op,p: S.Memo<U32,U32> & (M.Arena<S.Cell<U32,U32>> & Bool)) -> S.Memo<U32,U32> & (M.Arena<S.Cell<U32,U32>> & Bool):
  (m,q) = p
  (a,ok) = q
  compared(ok,model(a,op),actual(m,op))

def run(ops: List<&2,Op>,p: S.Memo<U32,U32> & (M.Arena<S.Cell<U32,U32>> & Bool)) -> Bool:
  match ops:
    case Nil{}:
      (m,q) = p
      (a,ok) = q
      ok
    case Con{op,rest}:
      run(rest,advance(op,p))

def start(ops: List<&2,Op>,r: Result<S.Error,S.Memo<U32,U32>>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{m}: run(ops,(m,(M.Arena{11,3n,Nil{}},True{})))

def created(ops: List<&2,Op>,p: S.Scopes & Result<S.Error,S.Memo<U32,U32>>) -> Bool:
  (scopes,r) = p
  start(ops,r)

def trace(ops: List<&2,Op>) -> Bool:
  created(ops,S.Memo.new(U32,U32,S.Scopes.from(11),3))

def witness() -> Bool:
  trace([Observe{S.Id{11,0}},Add{},Add{},Add{},Add{},Observe{S.Id{11,0}},
    Apply{S.Id{11,0},S.Succeed{17}},Apply{S.Id{11,0},S.Reject{23}},Apply{S.Id{11,0},S.Cancel{}},
    Apply{S.Id{11,0},S.Begin{}},Observe{S.Id{11,0}},Apply{S.Id{11,0},S.Begin{}},
    Apply{S.Id{11,0},S.Cancel{}},Observe{S.Id{11,0}},Apply{S.Id{11,0},S.Begin{}},
    Apply{S.Id{11,0},S.Succeed{37}},Observe{S.Id{11,0}},
    Apply{S.Id{11,0},S.Begin{}},Apply{S.Id{11,0},S.Succeed{41}},
    Apply{S.Id{11,0},S.Reject{43}},Apply{S.Id{11,0},S.Cancel{}},Observe{S.Id{11,0}},
    Apply{S.Id{11,1},S.Begin{}},Apply{S.Id{11,1},S.Reject{53}},Observe{S.Id{11,1}},
    Apply{S.Id{11,1},S.Begin{}},Apply{S.Id{11,1},S.Succeed{59}},
    Apply{S.Id{11,1},S.Reject{61}},Apply{S.Id{11,1},S.Cancel{}},Observe{S.Id{11,1}},
    Apply{S.Id{12,0},S.Begin{}},Apply{S.Id{11,3},S.Begin{}},
    Apply{S.Id{11,4294967295},S.Begin{}},Observe{S.Id{12,0}},Observe{S.Id{11,3}}])

# Review regression: grow AFTER terminal cells exist, and exhaust while busy.
def interleaved_witness() -> Bool:
  trace([Add{},Apply{S.Id{11,0},S.Begin{}},Apply{S.Id{11,0},S.Succeed{37}},
    Add{},Observe{S.Id{11,0}},Apply{S.Id{11,1},S.Begin{}},Apply{S.Id{11,1},S.Reject{53}},
    Add{},Observe{S.Id{11,0}},Observe{S.Id{11,1}},Apply{S.Id{11,2},S.Begin{}},
    Add{},Observe{S.Id{11,2}},Observe{S.Id{11,0}},Observe{S.Id{11,1}}])
