import Base

def shown(result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.print(String.concat(["Fail ",U32.show(code)," ",message]))
    case Done{file}: File.close(file)

def attempt(+label: String, mode: String) -> IO(Unit):
  do IO<Unit>:
    IO.print(label)
    IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open("a\0b",mode),shown)

# A path holding NUL is refused before the mode is examined.
def main() -> IO(Unit):
  do IO<Unit>:
    attempt("mode r","r")
    attempt("mode w","w")
    attempt("mode q","q")
