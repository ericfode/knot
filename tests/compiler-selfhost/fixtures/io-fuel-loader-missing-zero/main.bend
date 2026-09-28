# Twin of io-fuel-loader: the loader's dispatcher has no `case 0n _` row.
import Base

type Problem is Data:
  Missing{}
  Exhausted{}

type Action is Data:
  Stopped{error: Problem}
  Finished{seen: List<&2,String>}
  Advance{tasks: List<&2,String>, seen: List<&2,String>}
  Read{path: String, tasks: List<&2,String>, seen: List<&2,String>}

def read_result(result: Result<&1,&1,U32 & String,String>, next: Result<Problem,String> -> IO(Unit)) -> IO(Unit):
  match result:
    case Fail{(code,message)}: next(Fail{Missing{}})
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

def plan(tasks: List<&2,String>, seen: List<&2,String>) -> Action:
  match tasks:
    case Nil{}: Finished{List.reverse(&2,String,seen)}
    case Con{path,rest}: Read{path,rest,seen}

def follow(text: String, tasks: List<&2,String>) -> List<&2,String>:
  match text:
    case SNil{}: tasks
    case SCon{c,rest}: Con{SCon{c,rest},tasks}

def received(result: Result<Problem,String>, path: String, tasks: List<&2,String>, seen: List<&2,String>) -> Action:
  match result:
    case Fail{error}: Stopped{error}
    case Done{text}: Advance{follow(text,tasks),Con{path,seen}}

def run(fuel: Nat, action: Action, next: Result<Problem,List<&2,String>> -> IO(Unit)) -> IO(Unit):
  match fuel action:
    case _ Stopped{error}: next(Fail{error})
    case _ Finished{seen}: next(Done{seen})
    case 1n+ +n Advance{tasks,seen}: run(n,plan(tasks,seen),next)
    case 1n+ +n Read{+path,tasks,seen}:
      load(path,result => run(n,received(result,path,tasks,seen),next))

def joined(names: List<&2,String>) -> String:
  match names:
    case Nil{}: ""
    case Con{name,Nil{}}: name
    case Con{name,rest}: String.concat([name,",",joined(rest)])

def report(result: Result<Problem,List<&2,String>>) -> IO(Unit):
  match result:
    case Fail{Missing{}}: IO.print("missing")
    case Fail{Exhausted{}}: IO.print("exhausted")
    case Done{names}: IO.print(joined(names))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{start,Nil{}}: run(16n,Advance{Con{start,Nil{}},Nil{}},report)
    case _: IO.die(Unit,5,"expected one path")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
