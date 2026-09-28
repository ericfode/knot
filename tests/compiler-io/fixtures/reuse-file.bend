import Base

# File.read hands the handle back in its pair; the original handle is spent.
def after(file: File, pair: File & Result<&1,&1,U32 & String,String>) -> IO(Unit):
  (again,result) = pair
  do IO<Unit>:
    File.close(again)
    File.close(file)

def opened(result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,message)
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,String>,Unit,File.read(file,8),pair => after(file,pair))

def main() -> IO(Unit):
  IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open("small.txt","r"),opened)
