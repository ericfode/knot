import Base

# IO.try and IO.pass turn a host Fail{(code,message)} into IO.die(code,message).
def contents(pair: File & Result<&1,&1,U32 & String,String>) -> IO(String):
  (file,result) = pair
  do IO<String>:
    File.close(file)
    IO.pass(String,result)

def opened(file: File) -> IO(Unit):
  IO.bind(String,Unit,IO.bind(File & Result<&1,&1,U32 & String,String>,String,File.read(file,65537),contents),text => IO.print(text))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Nil{}}: IO.bind(File,Unit,IO.try(File,File.open(path,"r")),opened)
    case _: IO.die(Unit,99,"usage: path")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
