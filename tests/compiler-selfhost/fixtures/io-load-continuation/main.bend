# A user `load(path, next: X -> IO(Unit))` threaded through IO.bind lambdas
# across several user defs (src/load.bend:120-142, src/driver.bend:15-55); the
# second continuation captures the first one's result.
import Base

type Problem is Data:
  Missing{}
  Host{code: U32}

def read_result(result: Result<&1,&1,U32 & String,String>, next: Result<Problem,String> -> IO(Unit)) -> IO(Unit):
  match result:
    case Fail{(code,message)}: next(Fail{Host{code}})
    case Done{text}: next(Done{text})

def read_pair(pair: File & Result<&1,&1,U32 & String,String>, next: Result<Problem,String> -> IO(Unit)) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    read_result(result,next)

def opened(result: Result<&1,&1,U32 & String,File>, next: Result<Problem,String> -> IO(Unit)) -> IO(Unit):
  match result:
    case Fail{(code,message)}: next(Fail{Missing{}})
    case Done{file}:
      IO.bind(File & Result<&1,&1,U32 & String,String>,Unit,File.read(file,4096),pair => read_pair(pair,next))

def load(path: String, next: Result<Problem,String> -> IO(Unit)) -> IO(Unit):
  IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),result => opened(result,next))

def report(result: Result<Problem,String>) -> String:
  match result:
    case Fail{Missing{}}: "missing"
    case Fail{Host{code}}: String.append("host ",U32.show(code))
    case Done{text}: text

def both(first: String, second: String) -> IO(Unit):
  load(first,a => load(second,b => IO.print(String.concat([report(a),"+",report(b)]))))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{first,Con{second,Nil{}}}: both(first,second)
    case _: IO.die(Unit,5,"expected two paths")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
