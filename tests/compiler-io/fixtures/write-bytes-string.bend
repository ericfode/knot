import Base

# File.write_bytes takes a byte list, not a String.
def opened(result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,message)
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,Unit>,Unit,File.write_bytes(file,"abc"),pair => IO.print("written"))

def main() -> IO(Unit):
  IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open("out.bin","w"),opened)
