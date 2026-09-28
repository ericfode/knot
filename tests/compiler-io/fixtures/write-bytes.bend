import Base

# The compile-cli write path: open "w", one File.write_bytes, close, then report Built.
def failure(stage: String, code: U32, message: String) -> IO(Unit):
  IO.die(Unit,5,String.concat(["HostFailure\t",stage,"\t",U32.show(code),"\t",message]))

def ramp(n: Nat, +k: U32, acc: List<&2,U32>) -> List<&2,U32>:
  match n:
    case 0n: acc
    case 1n+p: ramp(p,U32.sub(k,1),Con{U32.and(U32.sub(k,1),255),acc})

def written(result: Result<&1,&1,U32 & String,Unit>, count: U32) -> IO(Unit):
  match result:
    case Fail{(code,message)}: failure("write",code,message)
    case Done{u}: IO.print(String.append("Built\t",U32.show(count)))

def write_pair(pair: File & Result<&1,&1,U32 & String,Unit>, count: U32) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    written(result,count)

def output_opened(result: Result<&1,&1,U32 & String,File>, bytes: List<&2,U32>, count: U32) -> IO(Unit):
  match result:
    case Fail{(code,message)}: failure("output-open",code,message)
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,Unit>,Unit,File.write_bytes(file,bytes),pair => write_pair(pair,count))

def configured(path: String, value: Maybe<&2,U32>) -> IO(Unit):
  match value:
    case Some{+n}: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"w"),result => output_opened(result,ramp(U32.to_nat(n),n,Nil{}),n))
    case None{}: IO.die(Unit,5,"HostFailure\targuments\texpected-u32")

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Con{count,Nil{}}}: configured(path,U32.read(count))
    case _: IO.die(Unit,5,"HostFailure\targuments\texpected output count")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
