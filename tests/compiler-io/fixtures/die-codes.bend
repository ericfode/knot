import Base

def code(value: Maybe<&2,U32>) -> U32:
  match value:
    case Some{x}: x
    case None{}: 99

def stop(args: List<String>) -> IO(Unit):
  match args:
    case Con{text,Nil{}}: IO.die(Unit,code(U32.read(text)),"stop")
    case _: IO.die(Unit,99,"usage: code")

def main() -> IO(Unit):
  do IO<Unit>:
    IO.print("before")
    IO.bind(List<String>,Unit,IO.args(),stop)
