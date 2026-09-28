import Base
import ./model.bend as M

def stopped(stop: M.Stop) -> IO(Unit):
  match stop:
    case M.Exhausted{kind,cause}: IO.die(Unit,4,String.concat(["Exhausted\tvm\t",U32.show(kind),"\t",cause]))
    case M.Refused{phase,code}: IO.die(Unit,5,String.concat(["HostFailure\t",phase,"\t",code]))
    case M.Unsupported{phase,code}: IO.die(Unit,3,String.concat(["Unsupported\t",phase,"\t",code]))
    case M.Internal{code}: IO.die(Unit,6,String.concat(["InternalFailure\tvm\t",code]))
    case M.Bound{code}: IO.die(Unit,7,String.concat(["HarnessBound\tmodel\t",code]))

def checked(result: Result<M.Stop,M.Plan>) -> IO(Unit):
  match result:
    case Fail{stop}: stopped(stop)
    case Done{plan}: IO.print("admitted")

def loaded(result: Result<&1,&1,U32 & String,List<&2,U32>>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\tread\t",U32.show(code),"\t",message]))
    case Done{bytes}: checked(M.load(bytes))

def read_pair(pair: File & Result<&1,&1,U32 & String,List<&2,U32>>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    loaded(result)

def opened(result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\topen\t",U32.show(code),"\t",message]))
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,List<&2,U32>>,Unit,File.read_bytes(file,16777217),read_pair)

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,rest}: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),opened)
    case Nil{}: IO.die(Unit,5,"HostFailure\targuments\texpected IMAGE")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
