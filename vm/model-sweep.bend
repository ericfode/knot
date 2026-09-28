import Base
import ./model/word.bend as W
import ./model/audit.bend as A
import ./model-cli.bend as C

# The bounded validator-soundness sweep: every single-word mutation of an
# image (A.mutations) is refused with a reason, or runs soundly (A.sound).
# One line per mutation: position, variant (0 zero, 1 successor, 2 predecessor),
# then `refused` and the refusal, or `ran`, the outcome and the verdict.

def line(run: A.Run) -> String:
  match run:
    case A.Refusal{stop}: String.append("refused\t",C.stop_line(stop))
    case A.Ran{code,m,ok}: String.append("ran\t",C.outcome_name(C.machine_outcome(m)))

def verdict(+j: U32, +run: A.Run) -> String:
  +head = String.concat([U32.show(U32.div(j,3)),"\t",U32.show(U32.mod(j,3)),"\t"])
  W.choose(String,A.sound(run),u => String.concat([head,line(run),"\tsound"]),u => String.concat([head,line(run),"\tunsound"]))

def swept(images: List<&2,List<&2,U32>>, +fuel: U32, +j: U32) -> IO(Unit):
  match images:
    case Nil{}: IO.pure(Unit,Unit{})
    case Con{+w,rest}:
      IO.bind(Unit,Unit,IO.print(verdict(j,A.run_words(w,U32.to_nat(16777216),fuel))),u => swept(rest,fuel,U32.add(j,1)))

def sweep(+bytes: List<&2,U32>, budget: String) -> IO(Unit):
  +words = W.pack(bytes)
  C.fuel(U32.read(budget),+f => swept(A.mutations(U32.to_nat(W.count(U32,words)),words,0),f,0))

def read_result(result: Result<&1,&1,U32 & String,List<&2,U32>>, budget: String) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\tread\t",U32.show(code),"\t",message]))
    case Done{bytes}: sweep(bytes,budget)

def read_pair(pair: File & Result<&1,&1,U32 & String,List<&2,U32>>, budget: String) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    read_result(result,budget)

def opened(result: Result<&1,&1,U32 & String,File>, budget: String) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\topen\t",U32.show(code),"\t",message]))
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,List<&2,U32>>,Unit,File.read_bytes(file,16777217),pair => read_pair(pair,budget))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Con{budget,Nil{}}}: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),result => opened(result,budget))
    case _: C.stopped(W.Refused{"arguments","expected IMAGE FUEL"})

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
