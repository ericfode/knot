import Base

def choose(-A: Type, condition: Bool, yes: Unit -> A, no: Unit -> A) -> A:
  match condition:
    case True{}: yes(Unit{})
    case False{}: no(Unit{})

# The handle and the write result are dropped unclosed; the bytes stay written.
def after(pair: File & Result<&1,&1,U32 & String,Unit>) -> IO(Unit):
  (file,result) = pair
  IO.die(Unit,3,"after write")

def opened(result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,message)
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,Unit>,Unit,File.write_bytes(file,[75,78,79,84]),after)

def run(+mode: String, path: String) -> IO(Unit):
  choose(IO(Unit),String.eq(mode,"before"),u => IO.die(Unit,3,"before open"),u =>
    IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"w"),opened))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{mode,Con{path,Nil{}}}: run(mode,path)
    case _: IO.die(Unit,99,"usage: before|after path")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
