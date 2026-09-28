import Base

def codes(s: String) -> String:
  match s:
    case SNil{}: ""
    case SCon{c,t}: String.concat([" ",U32.show(Char.to_u32(c)),codes(t)])

def read_result(result: Result<&1,&1,U32 & String,String>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,message)
    case Done{+text}:
      do IO<Unit>:
        IO.print(String.append("text ",text))
        IO.print(String.append("codes",codes(text)))

def read_pair(pair: File & Result<&1,&1,U32 & String,String>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    read_result(result)

def reopened(result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,message)
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,String>,Unit,File.read(file,64),read_pair)

# The write is closed before the same path is reopened for reading.
def write_pair(+path: String, pair: File & Result<&1,&1,U32 & String,Unit>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),reopened)

def opened(+path: String, result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,message)
    case Done{file}:
      IO.bind(File & Result<&1,&1,U32 & String,Unit>,Unit,File.write_bytes(file,[104,195,169,108,108,111,32,240,159,152,128,10]),write_pair(path))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{+path,Nil{}}: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"w"),opened(path))
    case _: IO.die(Unit,99,"usage: path")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
