import Base

def stop(args: List<String>) -> IO(Unit):
  match args:
    case Con{message,Nil{}}: IO.die(Unit,3,message)
    case Nil{}: IO.die(Unit,3,String.concat(["HostFailure","\t","read","\t",U32.show(21),"\t","Is a directory"]))
    case _: IO.die(Unit,99,"usage: [message]")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),stop)
