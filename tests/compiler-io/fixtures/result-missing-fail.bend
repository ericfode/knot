import Base

# Every host result must handle Fail.
def opened(result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Done{file}: File.close(file)

def main() -> IO(Unit):
  IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open("small.txt","r"),opened)
