import Base

def write_result(result: Result<&1,&1,U32 & String,Unit>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.print(String.concat(["write Fail ",U32.show(code)," ",message]))
    case Done{u}: IO.print("write Done")

def read_result(result: Result<&1,&1,U32 & String,String>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.print(String.concat(["read Fail ",U32.show(code)," ",message]))
    case Done{text}: IO.print(String.append("read Done ",text))

def read_pair(pair: File & Result<&1,&1,U32 & String,String>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    read_result(result)

def write_pair(pair: File & Result<&1,&1,U32 & String,Unit>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    write_result(result)
    IO.bind(File & Result<&1,&1,U32 & String,String>,Unit,File.read(file,64),read_pair)

# Every handle is offered one write of "AB\n" and then one read.
def opened(result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.print(String.concat(["open Fail ",U32.show(code)," ",message]))
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,Unit>,Unit,File.write_bytes(file,[65,66,10]),write_pair)

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Con{mode,Nil{}}}: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,mode),opened)
    case _: IO.die(Unit,99,"usage: path mode")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
