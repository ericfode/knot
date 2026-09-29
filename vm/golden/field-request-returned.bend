import Base

type Box<-R: Type> is Type:
  B{x: IO.OP<R>}

def unbox(-R: Type, b: Box<R>) -> IO.OP<R>:
  match b:
    case B{x}:
      x

def run(m: IO(Unit)) -> IO(Unit):
  R => k => unbox(R, B{m(R, k)})

def main() -> IO(Unit):
  run(IO.print("boxed-then-returned"))
