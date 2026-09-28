import Base

# Source text in, one byte per Char out: every host failure is reported by stage.
def failure(stage: String, code: U32, message: String) -> IO(Unit):
  IO.die(Unit,5,String.concat(["HostFailure\t",stage,"\t",U32.show(code),"\t",message]))

def units(s: String) -> List<&2,U32>:
  match s:
    case SNil{}: Nil{}
    case SCon{c,t}: Con{Char.to_u32(c),units(t)}

def written(result: Result<&1,&1,U32 & String,Unit>, count: U32) -> IO(Unit):
  match result:
    case Fail{(code,message)}: failure("write",code,message)
    case Done{u}: IO.print(String.append("Built\t",U32.show(count)))

def write_pair(count: U32, pair: File & Result<&1,&1,U32 & String,Unit>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    written(result,count)

def output_opened(+bytes: List<&2,U32>, result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: failure("output-open",code,message)
    case Done{file}:
      IO.bind(File & Result<&1,&1,U32 & String,Unit>,Unit,File.write_bytes(file,bytes),write_pair(U32.from_nat(List.length(&2,U32,bytes))))

def read_result(output: String, result: Result<&1,&1,U32 & String,String>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: failure("read",code,message)
    case Done{text}: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(output,"w"),output_opened(units(text)))

def read_pair(output: String, pair: File & Result<&1,&1,U32 & String,String>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    read_result(output,result)

def opened(output: String, result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: failure("open",code,message)
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,String>,Unit,File.read(file,65537),read_pair(output))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{source,Con{output,Nil{}}}: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(source,"r"),opened(output))
    case _: IO.die(Unit,5,"HostFailure\targuments\texpected source output")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
