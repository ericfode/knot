import Base
import ./model.bend as M

# The model's command line mirrors the VM's (VM-DESIGN §2): a Book image takes
# `IMAGE FN FUEL [ORDINALS...]`, a Program image `IMAGE FUEL -- [ARGS...]`.
# Outcomes print as classification, phase and code on stderr with eval-cli's
# exit statuses; the model's own transition bound exits 7.

def stopped(stop: M.Stop) -> IO(Unit):
  match stop:
    case M.Exhausted{kind,cause}: IO.die(Unit,4,String.concat(["Exhausted\tvm\t",U32.show(kind),"\t",cause]))
    case M.Refused{phase,code}: IO.die(Unit,5,String.concat(["HostFailure\t",phase,"\t",code]))
    case M.Unsupported{phase,code}: IO.die(Unit,3,String.concat(["Unsupported\t",phase,"\t",code]))
    case M.Internal{code}: IO.die(Unit,6,String.concat(["InternalFailure\tvm\t",code]))
    case M.Bound{code}: IO.die(Unit,7,String.concat(["HarnessBound\tmodel\t",code]))

def utf8(codes: List<&2,U32>) -> List<&2,U32>:
  match codes:
    case Nil{}: Nil{}
    case Con{+c,+rest}:
      M.choose(List<&2,U32>,U32.is_lt(c,128),u => Con{c,utf8(rest)},u =>
      M.choose(List<&2,U32>,U32.is_lt(c,2048),u => Con{U32.add(192,U32.shrn(c,6n)),Con{U32.add(128,U32.and(c,63)),utf8(rest)}},u =>
      M.choose(List<&2,U32>,U32.is_lt(c,65536),u => Con{U32.add(224,U32.shrn(c,12n)),Con{U32.add(128,U32.and(U32.shrn(c,6n),63)),Con{U32.add(128,U32.and(c,63)),utf8(rest)}}},u =>
        Con{U32.add(240,U32.shrn(c,18n)),Con{U32.add(128,U32.and(U32.shrn(c,12n),63)),Con{U32.add(128,U32.and(U32.shrn(c,6n),63)),Con{U32.add(128,U32.and(c,63)),utf8(rest)}}}})))

def lines(out: List<&2,List<&2,U32>>, done: IO(Unit)) -> IO(Unit):
  match out:
    case Nil{}: done
    case Con{line,rest}: IO.bind(Unit,Unit,IO.print(M.codes_text(line)),u => lines(rest,done))

def concluded(outcome: M.Outcome) -> IO(Unit):
  match outcome:
    case M.Described{result,tag,tree}: IO.print(String.concat(["Evaluated\t",U32.show(result),"\t",U32.show(tag),"\t",M.codes_text(tree)]))
    case M.Emitted{}: IO.pure(Unit,Unit{})
    case M.Died{code,message}: IO.die(Unit,code,M.codes_text(message))
    case M.Stopped{stop}: stopped(stop)
    case M.Answered{w}: stopped(M.Internal{"undescribed answer"})

def reported(m: M.Machine) -> IO(Unit):
  match m:
    case M.Machine{M.Finished{outcome},stack,heap,meter,out}: lines(List.reverse(&2,List<&2,U32>,out),concluded(outcome))
    case _: stopped(M.Internal{"unfinished machine"})

def bound() -> Nat:
  U32.to_nat(4294967295)

def settled(result: Result<M.Stop,M.Machine>) -> IO(Unit):
  match result:
    case Fail{stop}: stopped(stop)
    case Done{m}: reported(m)

def fuel(value: Maybe<&2,U32>, next: U32 -> IO(Unit)) -> IO(Unit):
  match value:
    case None{}: stopped(M.Refused{"arguments","expected-u32"})
    case Some{x}: next(x)

def ordinal(value: Maybe<&2,U32>) -> Result<M.Stop,U32>:
  match value:
    case None{}: Fail{M.Refused{"arguments","expected-u32"}}
    case Some{x}: Done{x}

def ordinals(values: List<String>) -> Result<M.Stop,List<&2,U32>>:
  match values:
    case Nil{}: Done{Nil{}}
    case Con{head,tail}:
      M.bind(U32,List<&2,U32>,ordinal(U32.read(head)),x =>
        M.bind(List<&2,U32>,List<&2,U32>,ordinals(tail),xs => Done{Con{x,xs}}))

def run_book(+plan: M.Plan, +booted: M.Booted, name: String, budget: String, values: List<String>) -> IO(Unit):
  +bytes = utf8(M.text(name))
  +code = M.code_of(booted)
  fuel(U32.read(budget),+f =>
    settled(M.bind(List<&2,U32>,M.Machine,ordinals(values),xs =>
      M.bind(M.Machine,M.Machine,M.book(plan,booted,bytes,f,xs),m =>
        M.concluded(code,M.result_type(plan,bytes),M.run(bound(),code,m))))))

def run_program(+plan: M.Plan, +booted: M.Booted, budget: String) -> IO(Unit):
  fuel(U32.read(budget),f => reported(M.run(bound(),M.code_of(booted),M.program(plan,booted,f))))

def entry_of(plan: M.Plan) -> U32:
  match plan:
    case M.Plan{entry,types,functions,reps}: entry

def started(+plan: M.Plan, +booted: M.Booted, args: List<String>) -> IO(Unit):
  match args:
    case Con{+name,Con{budget,values}}:
      M.choose(IO(Unit),U32.is_eq(entry_of(plan),0),u => run_book(plan,booted,name,budget,values),u => run_program(plan,booted,name))
    case _: stopped(M.Refused{"arguments","expected FN FUEL or FUEL --"})

def booted_start(result: Result<M.Stop,M.Booted>, +plan: M.Plan, args: List<String>) -> IO(Unit):
  match result:
    case Fail{stop}: stopped(stop)
    case Done{booted}: started(plan,booted,args)

def settled_start(result: Result<M.Stop,M.Plan>, +bytes: List<&2,U32>, args: List<String>) -> IO(Unit):
  match result:
    case Fail{stop}: stopped(stop)
    case Done{+plan}: booted_start(M.boot(M.pack(bytes)),plan,args)

def loaded(+bytes: List<&2,U32>, args: List<String>) -> IO(Unit):
  settled_start(M.load(bytes),bytes,args)

def read_result(result: Result<&1,&1,U32 & String,List<&2,U32>>, args: List<String>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\tread\t",U32.show(code),"\t",message]))
    case Done{bytes}: loaded(bytes,args)

def read_pair(pair: File & Result<&1,&1,U32 & String,List<&2,U32>>, args: List<String>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    read_result(result,args)

def opened(result: Result<&1,&1,U32 & String,File>, args: List<String>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\topen\t",U32.show(code),"\t",message]))
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,List<&2,U32>>,Unit,File.read_bytes(file,16777217),pair => read_pair(pair,args))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,rest}: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),result => opened(result,rest))
    case Nil{}: stopped(M.Refused{"arguments","expected IMAGE"})

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
