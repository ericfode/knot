import Base
import ./model/word.bend as W
import ./model/validate.bend as V
import ./model/encode.bend as E
import ./model/memory.bend as H
import ./model/machine.bend as M
import ./model/audit.bend as A

# The model's command line mirrors the VM's (VM-DESIGN §2): a Book image takes
# `IMAGE FN FUEL [ORDINALS...]`, a Program image `IMAGE FUEL -- [ARGS...]`.
# Outcomes print as classification, phase and code on stderr with eval-cli's
# exit statuses; the model's own transition bound exits 7.

def stop_line(stop: W.Stop) -> String:
  match stop:
    case W.Exhausted{kind,cause}: String.concat(["Exhausted\tvm\t",U32.show(kind),"\t",cause])
    case W.Refused{phase,code}: String.concat(["HostFailure\t",phase,"\t",code])
    case W.Unsupported{phase,code}: String.concat(["Unsupported\t",phase,"\t",code])
    case W.Internal{code}: String.append("InternalFailure\tvm\t",code)
    case W.Bound{code}: String.append("HarnessBound\tmodel\t",code)

def stop_status(stop: W.Stop) -> U32:
  match stop:
    case W.Exhausted{kind,cause}: 4
    case W.Refused{phase,code}: 5
    case W.Unsupported{phase,code}: 3
    case W.Internal{code}: 6
    case W.Bound{code}: 7

def stopped(+stop: W.Stop) -> IO(Unit):
  IO.die(Unit,stop_status(stop),stop_line(stop))

def utf8(codes: List<&2,U32>) -> List<&2,U32>:
  match codes:
    case Nil{}: Nil{}
    case Con{+c,+rest}:
      W.choose(List<&2,U32>,U32.is_lt(c,128),u => Con{c,utf8(rest)},u =>
      W.choose(List<&2,U32>,U32.is_lt(c,2048),u => Con{U32.add(192,U32.shrn(c,6n)),Con{U32.add(128,U32.and(c,63)),utf8(rest)}},u =>
      W.choose(List<&2,U32>,U32.is_lt(c,65536),u => Con{U32.add(224,U32.shrn(c,12n)),Con{U32.add(128,U32.and(U32.shrn(c,6n),63)),Con{U32.add(128,U32.and(c,63)),utf8(rest)}}},u =>
        Con{U32.add(240,U32.shrn(c,18n)),Con{U32.add(128,U32.and(U32.shrn(c,12n),63)),Con{U32.add(128,U32.and(U32.shrn(c,6n),63)),Con{U32.add(128,U32.and(c,63)),utf8(rest)}}}})))

def lines(out: List<&2,List<&2,U32>>, done: IO(Unit)) -> IO(Unit):
  match out:
    case Nil{}: done
    case Con{line,rest}: IO.bind(Unit,Unit,IO.print(V.codes_text(line)),u => lines(rest,done))

def concluded(outcome: M.Outcome) -> IO(Unit):
  match outcome:
    case M.Described{result,tag,tree}: IO.print(String.concat(["Evaluated\t",U32.show(result),"\t",U32.show(tag),"\t",V.codes_text(tree)]))
    case M.Emitted{}: IO.pure(Unit,Unit{})
    case M.Died{code,message}: IO.die(Unit,code,V.codes_text(message))
    case M.Stopped{stop,pending}: stopped(stop)
    case M.Answered{w}: stopped(W.Internal{"undescribed answer"})

def reported(m: M.Machine) -> IO(Unit):
  match m:
    case M.Machine{M.Finished{outcome},stack,heap,meter,out}: lines(List.reverse(&2,List<&2,U32>,out),concluded(outcome))
    case _: stopped(W.Internal{"unfinished machine"})

def bound() -> Nat:
  U32.to_nat(4294967295)

def settled(result: Result<W.Stop,M.Machine>) -> IO(Unit):
  match result:
    case Fail{stop}: stopped(stop)
    case Done{m}: reported(m)

def fuel(value: Maybe<&2,U32>, next: U32 -> IO(Unit)) -> IO(Unit):
  match value:
    case None{}: stopped(W.Refused{"arguments","expected-u32"})
    case Some{x}: next(x)

def ordinal(value: Maybe<&2,U32>) -> Result<W.Stop,U32>:
  match value:
    case None{}: Fail{W.Refused{"arguments","expected-u32"}}
    case Some{x}: Done{x}

def ordinals(values: List<String>) -> Result<W.Stop,List<&2,U32>>:
  match values:
    case Nil{}: Done{Nil{}}
    case Con{head,tail}:
      H.bind(U32,List<&2,U32>,ordinal(U32.read(head)),x =>
        H.bind(List<&2,U32>,List<&2,U32>,ordinals(tail),xs => Done{Con{x,xs}}))

def run_book(+plan: W.Plan, +booted: M.Booted, name: String, budget: String, values: List<String>) -> IO(Unit):
  +bytes = utf8(M.text(name))
  +code = M.code_of(booted)
  fuel(U32.read(budget),+f =>
    settled(H.bind(List<&2,U32>,M.Machine,ordinals(values),xs =>
      H.bind(M.Machine,M.Machine,M.book(plan,booted,bytes,f,xs),m =>
        M.concluded(code,M.result_type(plan,bytes),M.run(bound(),code,m))))))

def outcome_name(outcome: M.Outcome) -> String:
  match outcome:
    case M.Described{result,tag,tree}: "Described"
    case M.Emitted{}: "Emitted"
    case M.Died{code,message}: "Died"
    case M.Answered{w}: "Answered"
    case M.Stopped{W.Exhausted{k,c},pending}: "Exhausted"
    case M.Stopped{W.Refused{p,c},pending}: "HostFailure"
    case M.Stopped{W.Unsupported{p,c},pending}: "Unsupported"
    case M.Stopped{W.Internal{c},pending}: "InternalFailure"
    case M.Stopped{W.Bound{c},pending}: "HarnessBound"

def completes(outcome: M.Outcome) -> Bool:
  match outcome:
    case M.Described{result,tag,tree}: True{}
    case M.Emitted{}: True{}
    case M.Died{code,message}: True{}
    case _: False{}

def machine_outcome(m: M.Machine) -> M.Outcome:
  match m:
    case M.Machine{M.Finished{outcome},stack,heap,meter,out}: outcome
    case _: M.Stopped{W.Internal{"unfinished machine"},M.Eval{0}}

def calls_of(m: M.Machine) -> U32:
  match m:
    case M.Machine{control,stack,heap,M.Meter{fuel,calls,quantum},out}: calls

# The audit line: whether every transition balanced and a completed run
# released every mortal cell, the transitions audited, the outcome, the
# mortal cells still live and the entries paid for (SPEC §7's `calls`).
def audit_report(+code: H.Code, +m: M.Machine, +steps: U32, balanced: Bool) -> IO(Unit):
  +outcome = machine_outcome(m)
  +live = A.leaked(code,m)
  +passed = Bool.and(Bool.and(balanced,A.balanced(code,m)),Bool.or(Bool.not(completes(outcome)),U32.is_eq(live,0)))
  +line = String.concat(["audit\t",Bool.pick(String,passed,"passed","failed"),"\t",U32.show(steps),"\t",outcome_name(outcome),"\t",U32.show(live),"\t",U32.show(calls_of(m))])
  W.choose(IO(Unit),passed,u => IO.print(line),u => IO.die(Unit,6,line))

def audit_settled(+code: H.Code, result: Result<W.Stop,M.Machine>, +steps: U32, balanced: Bool) -> IO(Unit):
  match result:
    case Fail{stop}: stopped(stop)
    case Done{m}: audit_report(code,m,steps,balanced)

def audit_concluded(+code: H.Code, +t: U32, a: A.Audit) -> IO(Unit):
  match a:
    case A.Audit{m,+steps,balanced}: audit_settled(code,M.concluded(code,t,m),steps,balanced)

def audit_started(+code: H.Code, +t: U32, result: Result<W.Stop,M.Machine>) -> IO(Unit):
  match result:
    case Fail{stop}: stopped(stop)
    case Done{m}: audit_concluded(code,t,A.audited(bound(),code,m,0))

def audit_book(+plan: W.Plan, +booted: M.Booted, name: String, budget: String, values: List<String>) -> IO(Unit):
  +bytes = utf8(M.text(name))
  +code = M.code_of(booted)
  fuel(U32.read(budget),+f =>
    audit_started(code,M.result_type(plan,bytes),H.bind(List<&2,U32>,M.Machine,ordinals(values),xs => M.book(plan,booted,bytes,f,xs))))

def audit_program(+plan: W.Plan, +booted: M.Booted, budget: String) -> IO(Unit):
  +code = M.code_of(booted)
  fuel(U32.read(budget),f => audit_concluded(code,W.none(),A.audited(bound(),code,M.program(plan,booted,f),0)))

def run_program(+plan: W.Plan, +booted: M.Booted, budget: String) -> IO(Unit):
  fuel(U32.read(budget),f => reported(M.run(bound(),M.code_of(booted),M.program(plan,booted,f))))

def entry_of(plan: W.Plan) -> U32:
  match plan:
    case W.Plan{entry,types,functions,reps}: entry

def started(audit: Bool, +plan: W.Plan, +booted: M.Booted, args: List<String>) -> IO(Unit):
  match audit args:
    case False{} Con{+name,Con{budget,values}}:
      W.choose(IO(Unit),U32.is_eq(entry_of(plan),0),u => run_book(plan,booted,name,budget,values),u => run_program(plan,booted,name))
    case True{} Con{+name,Con{budget,values}}:
      W.choose(IO(Unit),U32.is_eq(entry_of(plan),0),u => audit_book(plan,booted,name,budget,values),u => audit_program(plan,booted,name))
    case _ _: stopped(W.Refused{"arguments","expected FN FUEL or FUEL --"})

def booted_start(result: Result<W.Stop,M.Booted>, audit: Bool, +plan: W.Plan, args: List<String>) -> IO(Unit):
  match result:
    case Fail{stop}: stopped(stop)
    case Done{booted}: started(audit,plan,booted,args)

def settled_start(result: Result<W.Stop,W.Plan>, audit: Bool, +bytes: List<&2,U32>, args: List<String>) -> IO(Unit):
  match result:
    case Fail{stop}: stopped(stop)
    case Done{+plan}: booted_start(M.boot(W.pack(bytes)),audit,plan,args)

def loaded(audit: Bool, +bytes: List<&2,U32>, args: List<String>) -> IO(Unit):
  settled_start(E.load(bytes),audit,bytes,args)

def read_result(result: Result<&1,&1,U32 & String,List<&2,U32>>, audit: Bool, args: List<String>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\tread\t",U32.show(code),"\t",message]))
    case Done{bytes}: loaded(audit,bytes,args)

def read_pair(pair: File & Result<&1,&1,U32 & String,List<&2,U32>>, audit: Bool, args: List<String>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    read_result(result,audit,args)

def opened(result: Result<&1,&1,U32 & String,File>, audit: Bool, args: List<String>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\topen\t",U32.show(code),"\t",message]))
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,List<&2,U32>>,Unit,File.read_bytes(file,16777217),pair => read_pair(pair,audit,args))

def image(audit: Bool, args: List<String>) -> IO(Unit):
  match args:
    case Con{path,rest}: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),result => opened(result,audit,rest))
    case Nil{}: stopped(W.Refused{"arguments","expected IMAGE"})

def arguments(args: List<String>) -> IO(Unit):
  image(False{},args)

# vm/model-audit.bend's entry: the RC audit before every transition, reported
# as one line instead of the run's own output.
def audit_arguments(args: List<String>) -> IO(Unit):
  image(True{},args)

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
