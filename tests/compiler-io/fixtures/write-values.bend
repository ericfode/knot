import Base

def prepend(head: Maybe<&2,U32>, tail: Maybe<&2,List<&2,U32>>) -> Maybe<&2,List<&2,U32>>:
  match head tail:
    case Some{x} Some{xs}: Some{Con{x,xs}}
    case _ _: None{}

def values(args: List<String>) -> Maybe<&2,List<&2,U32>>:
  match args:
    case Nil{}: Some{Nil{}}
    case Con{head,tail}: prepend(U32.read(head),values(tail))

def write_result(result: Result<&1,&1,U32 & String,Unit>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.print(String.concat(["write Fail ",U32.show(code)," ",message]))
    case Done{u}: IO.print("write Done")

def write_pair(pair: File & Result<&1,&1,U32 & String,Unit>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    write_result(result)

# A byte list holding any value past 255 is refused whole: nothing is written.
def opened(bytes: List<&2,U32>, result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,message)
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,Unit>,Unit,File.write_bytes(file,bytes),write_pair)

def parsed(path: String, bytes: Maybe<&2,List<&2,U32>>) -> IO(Unit):
  match bytes:
    case Some{xs}: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"w"),opened(xs))
    case None{}: IO.die(Unit,99,"usage: path [u32...]")

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,rest}: parsed(path,values(rest))
    case Nil{}: IO.die(Unit,99,"usage: path [u32...]")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
