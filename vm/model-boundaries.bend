import Base
import ./model/word.bend as W
import ./model/memory.bend as H
import ./model/machine.bend as M
import ./model/audit.bend as A

# Literal installed states for model-boundaries.json. The Activation owns one immediate input;
# alterations to that input, output or pending Return preserve the RC invariant.
def base() -> U32:
  H.heap_base(0)

def code() -> H.Code:
  H.Code{W.empty(),W.empty(),W.empty(),W.empty(),W.empty(),W.empty(),Nil{},0}

def heap(input: U32) -> H.Heap:
  H.Heap{H.filled(W.empty(),base(),1,4,[0,1,H.immediate(input)],8),U32.add(base(),8),H.zeros(29n)}

def output() -> List<&2,List<&2,U32>>:
  [[65],[67]]

def state(control: M.Control, input: U32, out: List<&2,List<&2,U32>>) -> M.Machine:
  M.Machine{control,H.Stack{U32.shln(base(),2n),[H.Top{0}],3},heap(input),M.Meter{10,17,0},out}

def before() -> M.Machine:
  state(M.Return{H.immediate(7)},42,output())

def stopped(pending: M.Control, input: U32, out: List<&2,List<&2,U32>>) -> M.Machine:
  M.halted(state(pending,input,out),W.Refused{"image","ill-typed"})

def unchanged() -> M.Machine:
  stopped(M.Return{H.immediate(7)},42,output())

def input_changed() -> M.Machine:
  stopped(M.Return{H.immediate(7)},43,output())

def output_changed() -> M.Machine:
  stopped(M.Return{H.immediate(7)},42,[[66],[67]])

def pending_changed() -> M.Machine:
  stopped(M.Return{H.immediate(8)},42,output())

def with_heap(m: M.Machine, h: H.Heap) -> M.Machine:
  match m:
    case M.Machine{control,stack,heap,meter,out}: M.Machine{control,stack,h,meter,out}

def with_stack(m: M.Machine, s: H.Stack) -> M.Machine:
  match m:
    case M.Machine{control,stack,heap,meter,out}: M.Machine{control,s,heap,meter,out}

def with_meter(m: M.Machine, q: M.Meter) -> M.Machine:
  match m:
    case M.Machine{control,stack,heap,meter,out}: M.Machine{control,stack,heap,q,out}

def atomic_input() -> Bool:
  A.atomic(before(),input_changed())

def atomic_output() -> Bool:
  A.atomic(before(),output_changed())

def atomic_pending() -> Bool:
  A.atomic(before(),pending_changed())

def identities(controls: List<&2,M.Control>) -> Bool:
  match controls:
    case Nil{}: True{}
    case Con{+c,rest}: Bool.and(A.same_control(c,c),identities(rest))

def control_identities() -> Bool:
  identities([M.Eval{1},M.Return{15},M.Enter{M.Callee{0},[15]},M.Enter{M.Held{15},[17]},
    M.Finished{M.Answered{15}},M.Finished{M.Described{1,2,[65]}},M.Finished{M.Emitted{}},M.Finished{M.Died{1,[65]}},
    M.Finished{M.Stopped{W.Exhausted{3,"frames"},M.Return{15}}},M.Finished{M.Stopped{W.Refused{"image","ill-typed"},M.Eval{1}}},
    M.Finished{M.Stopped{W.Unsupported{"vm","effect"},M.Return{15}}},M.Finished{M.Stopped{W.Internal{"case arm"},M.Return{15}}},
    M.Finished{M.Stopped{W.Bound{"transitions"},M.Finished{M.Answered{15}}}}])

def stopped_control(stop: W.Stop) -> M.Control:
  M.Finished{M.Stopped{stop,M.Return{15}}}

# The committed value-on image; check-model.py requires these words to equal its frozen encoding.
def value_on() -> List<&2,U32>:
  [1196247371,1,75,0,0,32,38,49,56,57,62,0,4294967295,4294967295,4294967295,4294967295,4294967295,
   4294967295,4294967295,4294967295,4294967295,4294967295,4294967295,4294967295,967372322,
   1597628945,3931068771,212603004,2186566430,3374278737,2120669052,453228302,1,5,0,0,0,2,2,5,0,0,1,
   0,5,0,1,2,0,1,6,3,0,0,0,58,0,1,4,3,0,1,4,3,4,1734437958,3,3,6710863,3,2,28239,3,4,1852399981]

def retains_debit(m: M.Machine, heap: H.Heap) -> Bool:
  match m:
    case M.Machine{M.Finished{M.Stopped{W.Exhausted{3,cause},M.Enter{M.Callee{0},Nil{}}}},H.Stack{0,Con{H.Bind{0},Con{H.Top{0},Nil{}}},4194304},h,M.Meter{0,18,1},Con{Con{120,Nil{}},Nil{}}}:
      Bool.and(String.eq(cause,"frames"),A.same_heap(h,heap))
    case _: False{}

# Install a full frame region instead of allocating four million words. A non-tail Enter cannot
# push its Call frame; its checked debit stands, and the rest of the stopped state is unchanged.
def debit_boundary(loaded: Result<W.Stop,M.Booted>) -> Bool:
  match loaded:
    case Fail{stop}: False{}
    case Done{M.Booted{+code,+heap}}:
      +prior : M.Machine = M.Machine{M.Enter{M.Callee{0},Nil{}},H.Stack{0,[H.Bind{0},H.Top{0}],4194304},heap,M.Meter{1,17,0},[[120]]}
      retains_debit(M.settled(M.step(code,prior),prior),heap)

def entry_frame_debit() -> Bool:
  debit_boundary(M.boot(value_on()))

def description_pending(outcome: M.Outcome) -> Bool:
  match outcome:
    case M.Stopped{W.Refused{"image","ill-typed"},M.Return{0}}: True{}
    case _: False{}

def description_checked(result: Result<W.Stop,M.Machine>) -> Bool:
  match result:
    case Done{+m}:
      Bool.and(description_pending(A.finished_outcome(m)),A.atomic(state(M.Return{0},42,output()),m))
    case _: False{}

def description_stop() -> Bool:
  description_checked(M.concluded(code(),0,state(M.Finished{M.Answered{0}},42,output())))

def line(name: String, value: Bool) -> String:
  String.concat([name,"\t",Bool.pick(String,value,"1","0")])

def rows() -> List<&2,String>:
  [line("balanced-before",A.balanced(code(),before())),
   line("balanced-input-change",A.balanced(code(),input_changed())),
   line("balanced-output-change",A.balanced(code(),output_changed())),
   line("balanced-pending-change",A.balanced(code(),pending_changed())),
   line("atomic-unchanged",A.atomic(before(),unchanged())),
   line("atomic-input-change",atomic_input()),
   line("atomic-unrelated-word-change",A.atomic(before(),with_heap(unchanged(),H.stored_word(heap(42),4,0,99)))),
   line("atomic-output-change",atomic_output()),
   line("atomic-output-order",A.atomic(before(),stopped(M.Return{15},42,[[67],[65]]))),
   line("atomic-output-line-count",A.atomic(before(),stopped(M.Return{15},42,[[65]]))),
   line("atomic-output-line-boundary",A.atomic(before(),stopped(M.Return{15},42,[[65,67],[]]))),
   line("atomic-pending-change",atomic_pending()),
   line("atomic-combined-changes",A.atomic(before(),stopped(M.Return{17},43,[[66],[67]]))),
   line("atomic-bump-change",A.atomic(before(),with_heap(unchanged(),H.Heap{H.memory_of(heap(42)),U32.add(base(),16),H.zeros(29n)}))),
   line("atomic-free-change",A.atomic(before(),with_heap(unchanged(),H.Heap{H.memory_of(heap(42)),U32.add(base(),8),H.replaced(H.zeros(29n),0,4)}))),
   line("atomic-act-change",A.atomic(before(),with_stack(unchanged(),H.Stack{0,[H.Top{0}],3}))),
   line("atomic-frame-change",A.atomic(before(),with_stack(unchanged(),H.Stack{U32.shln(base(),2n),[H.Top{1}],3}))),
   line("atomic-top-change",A.atomic(before(),with_stack(unchanged(),H.Stack{U32.shln(base(),2n),[H.Top{0}],4}))),
   line("atomic-meter-change",A.atomic(before(),with_meter(unchanged(),M.Meter{10,18,0}))),
   line("atomic-enter-debit",A.atomic(state(M.Enter{M.Callee{0},[]},42,output()),with_meter(stopped(M.Enter{M.Callee{0},[]},42,output()),M.Meter{9,18,1}))),
   line("atomic-return-debit",A.atomic(before(),with_meter(unchanged(),M.Meter{9,18,1}))),
   line("control-identities",control_identities()),
   line("control-eval-node",A.same_control(M.Eval{1},M.Eval{2})),
   line("control-enter-target-kind",A.same_control(M.Enter{M.Callee{1},[]},M.Enter{M.Held{1},[]})),
   line("control-enter-callee",A.same_control(M.Enter{M.Callee{1},[]},M.Enter{M.Callee{2},[]})),
   line("control-enter-held",A.same_control(M.Enter{M.Held{15},[]},M.Enter{M.Held{17},[]})),
   line("control-enter-operands",A.same_control(M.Enter{M.Callee{1},[15]},M.Enter{M.Callee{1},[17]})),
   line("control-answer-word",A.same_control(M.Finished{M.Answered{15}},M.Finished{M.Answered{17}})),
   line("control-description-type",A.same_control(M.Finished{M.Described{1,2,[65]}},M.Finished{M.Described{2,2,[65]}})),
   line("control-description-tag",A.same_control(M.Finished{M.Described{1,2,[65]}},M.Finished{M.Described{1,3,[65]}})),
   line("control-description-text",A.same_control(M.Finished{M.Described{1,2,[65]}},M.Finished{M.Described{1,2,[66]}})),
   line("control-death-code",A.same_control(M.Finished{M.Died{1,[65]}},M.Finished{M.Died{2,[65]}})),
   line("control-death-message",A.same_control(M.Finished{M.Died{1,[65]}},M.Finished{M.Died{1,[66]}})),
   line("control-stop-kind",A.same_control(stopped_control(W.Exhausted{2,"frames"}),stopped_control(W.Exhausted{3,"frames"}))),
   line("control-stop-cause",A.same_control(stopped_control(W.Exhausted{3,"heap"}),stopped_control(W.Exhausted{3,"frames"}))),
   line("control-stop-phase",A.same_control(stopped_control(W.Refused{"invoke","ill-typed"}),stopped_control(W.Refused{"image","ill-typed"}))),
   line("control-stop-code",A.same_control(stopped_control(W.Refused{"image","arity"}),stopped_control(W.Refused{"image","ill-typed"}))),
   line("control-stop-class",A.same_control(stopped_control(W.Refused{"vm","effect"}),stopped_control(W.Unsupported{"vm","effect"}))),
   line("control-unsupported-code",A.same_control(stopped_control(W.Unsupported{"vm","effect"}),stopped_control(W.Unsupported{"vm","foreign"}))),
   line("control-internal-code",A.same_control(stopped_control(W.Internal{"case arm"}),stopped_control(W.Internal{"slots"}))),
   line("control-bound-code",A.same_control(stopped_control(W.Bound{"transitions"}),stopped_control(W.Bound{"other"}))),
   line("control-nested-pending",A.same_control(stopped_control(W.Bound{"transitions"}),M.Finished{M.Stopped{W.Bound{"transitions"},M.Return{17}}})),
   line("control-constructor",A.same_control(M.Return{15},M.Eval{15})),
   line("entry-frame-debit",entry_frame_debit()),
   line("atomic-description-stop",description_stop())]

def printed(lines: List<&2,String>) -> IO(Unit):
  match lines:
    case Nil{}: IO.pure(Unit,Unit{})
    case Con{l,rest}: IO.bind(Unit,Unit,IO.print(l),u => printed(rest))

def main() -> IO(Unit):
  printed(rows())
