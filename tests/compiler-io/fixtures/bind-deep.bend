import Base

def climb(n: Nat, +total: U32) -> IO(U32):
  match n:
    case 0n: IO.pure(U32,total)
    case 1n+p: IO.bind(U32,U32,IO.pure(U32,U32.add(total,1)),next => climb(p,next))

def pile(n: Nat, action: IO(U32)) -> IO(U32):
  match n:
    case 0n: action
    case 1n+p: pile(p,IO.bind(U32,U32,action,x => IO.pure(U32,U32.add(x,1))))

def report(+label: String, total: U32) -> IO(Unit):
  IO.print(String.concat([label," ",U32.show(total)]))

# 100,000 right-nested and 100,000 left-nested binds; neither may grow the host stack.
def main() -> IO(Unit):
  do IO<Unit>:
    IO.bind(U32,Unit,climb(100000n,0),report("right"))
    IO.bind(U32,Unit,pile(100000n,IO.pure(U32,0)),report("left"))
