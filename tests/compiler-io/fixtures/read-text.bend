import Base

# The driver's read path: open "r", one read of at most 65537 bytes, close.
def failure(stage: String, code: U32, message: String) -> IO(Unit):
  IO.die(Unit,5,String.concat(["HostFailure\t",stage,"\t",U32.show(code),"\t",message]))

def read_result(result: Result<&1,&1,U32 & String,String>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: failure("read",code,message)
    case Done{text}: IO.print(String.append("Read\t",text))

def read_pair(pair: File & Result<&1,&1,U32 & String,String>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    read_result(result)

def opened(result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: failure("open",code,message)
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,String>,Unit,File.read(file,65537),read_pair)

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Nil{}}: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),opened)
    case _: IO.die(Unit,5,"HostFailure\targuments\texpected path")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
