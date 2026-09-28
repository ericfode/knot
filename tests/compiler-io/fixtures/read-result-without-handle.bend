import Base

def got(result: Result<&1,&1,U32 & String,String>) -> IO(Unit):
  IO.print("read")

# File.read answers File & Result, not a bare Result.
def opened(result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,message)
    case Done{file}: IO.bind(Result<&1,&1,U32 & String,String>,Unit,File.read(file,8),got)

def main() -> IO(Unit):
  IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open("small.txt","r"),opened)
