import Base

def wrap(-R: Type, x: R) -> IO.OP<R>:
  Emit{x}

def keep(-R: Type, x: IO.OP<IO.OP<R>>, y: IO.OP<R>) -> IO.OP<R>:
  y

def run(m: IO(Unit), n: IO(Unit)) -> IO(Unit):
  R => k => keep(R, wrap(IO.OP<R>, m(R, x => Halt{7, "unreached"})), n(R, k))

def main() -> IO(Unit):
  run(IO.print("in-emit-dropped"), IO.print("live"))
