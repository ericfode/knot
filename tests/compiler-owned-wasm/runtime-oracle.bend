import Base
import ./model.bend as M

type Command is Data:
  Allocate{slots: U32, value: U32}
  Release{pointer: U32}

def allocated(result: M.Allocation) -> M.Pool & U32:
  match result:
    case M.Allocated{pool,pointer}: (pool,0)
    case M.Rejected{pool,status}: (pool,status)

def transition(command: Command, pool: M.Pool) -> M.Pool & U32:
  match command:
    case Allocate{slots,value}: allocated(M.alloc(pool,slots,value))
    case Release{pointer}: M.release(pool,pointer)

def emit(pair: M.Pool & U32, next: M.Pool -> IO(Unit)) -> IO(Unit):
  (+pool,status) = pair
  do IO<Unit>:
    IO.print(List.show(~&2,~U32,~U32.show,Con{status,M.snapshot(pool)}))
    next(pool)

def run(remaining: List<&2,Command>, pool: M.Pool) -> IO(Unit):
  match remaining:
    case Nil{}: IO.pure(Unit,Unit{})
    case Con{head,tail}: emit(transition(head,pool),next => run(tail,next))

def main() -> IO(Unit):
  emit((M.initial(65536),0),pool => run([
    Allocate{0,7},Allocate{2,11},Release{65548},Allocate{0,9},Release{65564},
    Allocate{2,13},Release{65548},Release{65564},Release{65548},Allocate{1,17},Release{65588}],pool))
