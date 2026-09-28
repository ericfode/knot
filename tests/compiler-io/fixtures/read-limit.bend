import Base

def last(s: String, +code: U32) -> U32:
  match s:
    case SNil{}: code
    case SCon{c,t}: last(t,Char.to_u32(c))

def summary(+text: String) -> String:
  String.concat(["chars ",U32.show(U32.from_nat(String.length(text)))," last ",U32.show(last(text,0))])

def shown(result: Result<&1,&1,U32 & String,String>) -> String:
  match result:
    case Fail{(code,message)}: String.concat(["Fail ",U32.show(code)," ",message])
    case Done{text}: summary(text)

def second(pair: File & Result<&1,&1,U32 & String,String>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    IO.print(String.append("second ",shown(result)))
    File.close(file)

# A read returns at most max bytes; the rest waits for the next read.
def first(+max: U32, pair: File & Result<&1,&1,U32 & String,String>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    IO.print(String.append("first ",shown(result)))
    IO.bind(File & Result<&1,&1,U32 & String,String>,Unit,File.read(file,max),second)

def opened(+max: U32, result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,message)
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,String>,Unit,File.read(file,max),first(max))

def limit(path: String, value: Maybe<&2,U32>) -> IO(Unit):
  match value:
    case Some{+max}: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),opened(max))
    case None{}: IO.die(Unit,99,"usage: path max")

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Con{max,Nil{}}}: limit(path,U32.read(max))
    case _: IO.die(Unit,99,"usage: path max")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
