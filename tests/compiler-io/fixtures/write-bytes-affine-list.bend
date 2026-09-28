import Base

# File.write_bytes takes List<&2,U32>; an affine List<&1,U32> does not fit.
def opened(bytes: List<U32>, result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,message)
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,Unit>,Unit,File.write_bytes(file,bytes),pair => IO.print("written"))

def main() -> IO(Unit):
  IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open("out.bin","w"),result => opened([1,2],result))
