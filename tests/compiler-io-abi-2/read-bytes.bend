import Base

# Usage: path mode (bytes|text max)*. Each read prints its Result as numbers:
# raw bytes for File.read_bytes, Unicode scalar values for File.read.

def numbers(xs: List<&2,U32>) -> String:
  match xs:
    case Nil{}: ""
    case Con{x,t}: String.concat([" ",U32.show(x),numbers(t)])

def scalars(s: String) -> List<&2,U32>:
  match s:
    case SNil{}: Nil{}
    case SCon{c,t}: Con{Char.to_u32(c),scalars(t)}

def decoded(result: Result<&1,&1,U32 & String,String>) -> Result<&1,&1,U32 & String,List<&2,U32>>:
  match result:
    case Fail{e}: Fail{e}
    case Done{s}: Done{scalars(s)}

def shown(result: Result<&1,&1,U32 & String,List<&2,U32>>) -> String:
  match result:
    case Fail{(code,message)}: String.concat(["Fail ",U32.show(code)," ",message])
    case Done{xs}: String.append("Done",numbers(xs))

def text(pair: File & Result<&1,&1,U32 & String,String>) -> IO(File & Result<&1,&1,U32 & String,List<&2,U32>>):
  (file,result) = pair
  IO.pure(File & Result<&1,&1,U32 & String,List<&2,U32>>,(file,decoded(result)))

def read(raw: Bool, file: File, max: U32) -> IO(File & Result<&1,&1,U32 & String,List<&2,U32>>):
  match raw:
    case True{}: File.read_bytes(file,max)
    case False{}: IO.bind(File & Result<&1,&1,U32 & String,String>,File & Result<&1,&1,U32 & String,List<&2,U32>>,File.read(file,max),text)

def limit(value: Maybe<&2,U32>, raw: Bool, file: File) -> IO(File & Result<&1,&1,U32 & String,List<&2,U32>>):
  match value:
    case None{}: IO.die(File & Result<&1,&1,U32 & String,List<&2,U32>>,99,"usage: path mode (bytes|text max)*")
    case Some{max}: read(raw,file,max)

def report(next: File -> IO(Unit), pair: File & Result<&1,&1,U32 & String,List<&2,U32>>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    IO.print(shown(result))
    next(file)

def reads(ops: List<String>, file: File) -> IO(Unit):
  match ops:
    case Con{op,Con{max,rest}}:
      IO.bind(File & Result<&1,&1,U32 & String,List<&2,U32>>,Unit,limit(U32.read(max),String.eq(op,"bytes"),file),report(f => reads(rest,f)))
    case _: File.close(file)

def opened(ops: List<String>, result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,message)
    case Done{file}: reads(ops,file)

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Con{mode,ops}}: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,mode),opened(ops))
    case _: IO.die(Unit,99,"usage: path mode (bytes|text max)*")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
