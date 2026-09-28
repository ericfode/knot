import Base

# The handle is dropped without File.close; its written bytes remain.
def written(pair: File & Result<&1,&1,U32 & String,Unit>) -> IO(Unit):
  (file,result) = pair
  IO.print("dropped")

def opened(result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,message)
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,Unit>,Unit,File.write_bytes(file,[100,114,111,112,10]),written)

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Nil{}}: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"w"),opened)
    case _: IO.die(Unit,99,"usage: path")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
