import Base

type Box<-R: Type> is Type:
  B{x: IO.OP<R>}

def drop(-R: Type, b: Box<R>, y: IO.OP<R>) -> IO.OP<R>:
  y

def run(m: IO(Unit), n: IO(Unit)) -> IO(Unit):
  R => k => drop(R, B{m(R, x => Halt{7, "unreached"})}, n(R, k))

def main() -> IO(Unit):
  run(IO.print("boxed-dropped"), IO.print("live"))
