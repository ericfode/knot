import Base
import ./model/word.bend as W
import ./model/validate.bend as V
import ./model/encode.bend as E
import ./model/memory.bend as H
import ./model/machine.bend as M
import ./model/audit.bend as A
import ./model-cli.bend as C

# vm-lockstep's model side: the machine's complete state before its first
# transition and after each one, one line each, in the fields the VM's test
# build reads out of linear memory (tests/compiler-vm-lockstep/README.md):
#
#   step | control | act | fuel calls quantum | top | frames | bump | free | output | heap
#
# A frame is `kind,node,aux,n,value...`, top of the stack first, and `top` counts
# the words the frames occupy. The heap is every word from the heap base to the
# bump pointer. A Book's answer is described as part of the transition that
# returns it to Top, as the VM does. Arguments: `STRIDE FROM TO IMAGE FN FUEL
# [ORDINALS...]` or `STRIDE FROM TO IMAGE FUEL -- [ARGS...]`, the IMAGE forms of
# vm/model-cli.bend. A state is printed when its step is 0, is a multiple of
# STRIDE or lies in FROM..TO, and always when the machine has finished. A request
# the entry refuses before any entry has no states and prints one `R` line.

def spaced(ws: List<&2,U32>) -> String:
  match ws:
    case Nil{}: ""
    case Con{+w,rest}: String.append(" ",String.append(U32.show(w),spaced(rest)))

def commaed(ws: List<&2,U32>) -> String:
  match ws:
    case Nil{}: ""
    case Con{+w,rest}: String.append(",",String.append(U32.show(w),commaed(rest)))

def stop_text(s: W.Stop) -> String:
  match s:
    case W.Exhausted{kind,cause}: String.concat(["E:",U32.show(kind),":",cause])
    case W.Refused{phase,code}: String.concat(["F:",phase,":",code])
    case W.Unsupported{phase,code}: String.concat(["U:",phase,":",code])
    case W.Internal{code}: String.append("I:",code)
    case W.Bound{code}: String.append("B:",code)

def enter_text(t: M.Target, ops: List<&2,U32>) -> String:
  match t:
    case M.Callee{+f}: String.concat(["N F ",U32.show(f),spaced(ops)])
    case M.Held{+w}: String.concat(["N W ",U32.show(w),spaced(ops)])

# The control a stopped machine could not advance is never itself Finished.
def pending_text(c: M.Control) -> String:
  match c:
    case M.Eval{+node}: String.append("E ",U32.show(node))
    case M.Return{+w}: String.append("R ",U32.show(w))
    case M.Enter{target,ops}: enter_text(target,ops)
    case M.Finished{o}: "H"

def outcome_text(o: M.Outcome) -> String:
  match o:
    case M.Answered{+w}: String.append("A ",U32.show(w))
    case M.Described{+result,+tag,tree}: String.concat(["D ",U32.show(result)," ",U32.show(tag)," ",commaed(tree)])
    case M.Emitted{}: "X"
    case M.Died{+code,message}: String.concat(["Z ",U32.show(code)," ",commaed(message)])
    case M.Stopped{stop,pending}: String.concat(["S ",stop_text(stop),"@",pending_text(pending)])

def control_text(c: M.Control) -> String:
  match c:
    case M.Eval{+node}: String.append("E ",U32.show(node))
    case M.Return{+w}: String.append("R ",U32.show(w))
    case M.Enter{target,ops}: enter_text(target,ops)
    case M.Finished{o}: String.append("H ",outcome_text(o))

def padded(n: Nat, ws: List<&2,U32>) -> List<&2,U32>:
  match n ws:
    case 0n _: Nil{}
    case 1n+m Con{w,rest}: Con{w,padded(m,rest)}
    case 1n+m Nil{}: Con{0,padded(m,Nil{})}

# A Gather keeps its filled operands newest first and reserves `need` slots.
def frame_text(f: H.Frame) -> String:
  match f:
    case H.Top{+phase}: String.concat(["0,0,",U32.show(phase),",0"])
    case H.Gather{+node,+need,+got}:
      String.concat(["1,",U32.show(node),",",U32.show(W.count(U32,got)),",",U32.show(need),commaed(padded(U32.to_nat(need),List.reverse(&2,U32,got)))])
    case H.Bind{+node}: String.concat(["2,",U32.show(node),",0,0"])
    case H.Scope{+depth}: String.concat(["3,0,",U32.show(depth),",0"])
    case H.Call{+caller}: String.concat(["4,0,0,1,",U32.show(caller)])
    case H.InvokeFunction{+node}: String.concat(["5,",U32.show(node),",0,0"])
    case H.InvokeArgument{+node,+function}: String.concat(["6,",U32.show(node),",0,1,",U32.show(function)])

def frames_text(fs: List<&2,H.Frame>) -> String:
  match fs:
    case Nil{}: ""
    case Con{f,Nil{}}: frame_text(f)
    case Con{f,rest}: String.append(frame_text(f),String.append(";",frames_text(rest)))

def out_text(lines: List<&2,List<&2,U32>>) -> String:
  match lines:
    case Nil{}: ""
    case Con{line,Nil{}}: commaed(line)
    case Con{line,rest}: String.append(out_text(rest),String.append("/",commaed(line)))

def heap_text(n: Nat, +heap: H.Heap, +i: U32) -> String:
  match n:
    case 0n: ""
    case 1n+m: String.append(" ",String.append(U32.show(W.read(H.memory_of(heap),i)),heap_text(m,heap,U32.add(i,1))))

def state_text(+code: H.Code, +step: U32, m: M.Machine) -> String:
  match m:
    case M.Machine{control,H.Stack{+act,frames,+top},+heap,M.Meter{+fuel,+calls,+quantum},+out}:
      +base = A.base_of(code)
      +bump = A.bump_of(heap)
      String.concat([U32.show(step),"|",control_text(control),"|",U32.show(act),"|",U32.show(fuel)," ",U32.show(calls)," ",U32.show(quantum),"|",U32.show(top),"|",
        frames_text(frames),"|",U32.show(bump),"|",spaced(A.free_of(heap)),"|",U32.show(W.count(List<&2,U32>,out)),":",out_text(out),"|",
        heap_text(U32.to_nat(U32.sub(bump,base)),heap,base)])

# One transition: the step, and for a Book that returns its answer the
# description and drop that follow it.
def unwrapped(result: Result<W.Stop,M.Machine>, m: M.Machine) -> M.Machine:
  match result:
    case Done{next}: next
    case Fail{stop}: M.halted(m,stop)

def advanced(+code: H.Code, +t: U32, +m: M.Machine) -> M.Machine:
  unwrapped(M.concluded(code,t,M.settled(M.step(code,m),m)),m)

type Span is Data:
  Span{stride: U32, first: U32, last: U32}

def printed(+step: U32, w: Span, +done: Bool) -> Bool:
  match w:
    case Span{+stride,+first,+last}:
      W.or(W.or(done,U32.is_eq(step,0)),W.or(U32.is_eq(U32.mod(step,stride),0),Bool.and(U32.is_ge(step,first),U32.is_le(step,last))))

def traced(fuel: Nat, +code: H.Code, +t: U32, +m: M.Machine, +step: U32, +w: Span) -> IO(Unit):
  match fuel:
    case 0n: IO.print(state_text(code,step,M.halted(m,W.Bound{"transitions"})))
    case 1n+f:
      IO.bind(Unit,Unit,W.choose(IO(Unit),printed(step,w,M.is_finished(m)),u => IO.print(state_text(code,step,m)),u => IO.pure(Unit,Unit{})),u =>
        W.choose(IO(Unit),M.is_finished(m),u => IO.pure(Unit,Unit{}),u => traced(f,code,t,advanced(code,t,m),U32.add(step,1),w)))

def refused(stop: W.Stop) -> IO(Unit):
  IO.print(String.append("R ",C.stop_line(stop)))

def started(result: Result<W.Stop,M.Machine>, +code: H.Code, +t: U32, +w: Span) -> IO(Unit):
  match result:
    case Fail{stop}: refused(stop)
    case Done{m}: traced(C.bound(),code,t,m,0,w)

def traced_book(+plan: W.Plan, +booted: M.Booted, +w: Span, name: String, budget: String, values: List<String>) -> IO(Unit):
  +bytes = C.utf8(M.text(name))
  C.fuel(U32.read(budget),+f =>
    started(H.bind(List<&2,U32>,M.Machine,C.ordinals(values),xs => M.book(plan,booted,bytes,f,xs)),M.code_of(booted),M.result_type(plan,bytes),w))

def traced_program(+plan: W.Plan, +booted: M.Booted, +w: Span, budget: String) -> IO(Unit):
  C.fuel(U32.read(budget),f => started(Done{M.program(plan,booted,f)},M.code_of(booted),W.none(),w))

def booked(+plan: W.Plan, +booted: M.Booted, +w: Span, args: List<String>) -> IO(Unit):
  match args:
    case Con{name,Con{budget,values}}: traced_book(plan,booted,w,name,budget,values)
    case _: C.usage()

def programmed(+plan: W.Plan, +booted: M.Booted, +w: Span, args: List<String>) -> IO(Unit):
  match args:
    case Con{budget,Con{separator,rest}}: W.choose(IO(Unit),String.eq(separator,"--"),u => traced_program(plan,booted,w,budget),u => C.usage())
    case _: C.usage()

def dispatched(+plan: W.Plan, +booted: M.Booted, +w: Span, args: List<String>) -> IO(Unit):
  match plan:
    case W.Plan{0,types,functions,reps}: booked(plan,booted,w,args)
    case _: programmed(plan,booted,w,args)

def booted_start(result: Result<W.Stop,M.Booted>, +plan: W.Plan, +w: Span, args: List<String>) -> IO(Unit):
  match result:
    case Fail{stop}: C.stopped(stop)
    case Done{booted}: dispatched(plan,booted,w,args)

def settled_start(result: Result<W.Stop,W.Plan>, +bytes: List<&2,U32>, +w: Span, args: List<String>) -> IO(Unit):
  match result:
    case Fail{stop}: C.stopped(stop)
    case Done{+plan}: booted_start(M.boot(W.pack(bytes)),plan,w,args)

def loaded(+bytes: List<&2,U32>, +w: Span, args: List<String>) -> IO(Unit):
  settled_start(E.load(bytes),bytes,w,args)

def read_result(result: Result<&1,&1,U32 & String,List<&2,U32>>, +w: Span, args: List<String>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\tread\t",U32.show(code),"\t",message]))
    case Done{bytes}: loaded(bytes,w,args)

def read_pair(pair: File & Result<&1,&1,U32 & String,List<&2,U32>>, +w: Span, args: List<String>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    read_result(result,w,args)

def opened(result: Result<&1,&1,U32 & String,File>, +w: Span, args: List<String>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\topen\t",U32.show(code),"\t",message]))
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,List<&2,U32>>,Unit,File.read_bytes(file,16777217),pair => read_pair(pair,w,args))

def imaged(+w: Span, args: List<String>) -> IO(Unit):
  match args:
    case Con{path,rest}: IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),result => opened(result,w,rest))
    case Nil{}: C.usage()

def windowed(stride: Maybe<&2,U32>, first: Maybe<&2,U32>, last: Maybe<&2,U32>, args: List<String>) -> IO(Unit):
  match stride first last:
    case Some{+s} Some{+a} Some{+b}: imaged(Span{s,a,b},args)
    case _ _ _: C.usage()

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{stride,Con{first,Con{last,rest}}}: windowed(U32.read(stride),U32.read(first),U32.read(last),rest)
    case _: C.usage()

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
