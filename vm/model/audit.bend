import Base
import ./word.bend as W
import ./decode.bend as D
import ./encode.bend as E
import ./memory.bend as H
import ./machine.bend as M

# ---------------------------------------------------------------- the RC audit

def chase(fuel: Nat, +heap: H.Heap, +p: U32, +marks: W.Store) -> W.Store:
  match fuel:
    case 0n: marks
    case 1n+f: W.choose(W.Store,U32.is_eq(p,0),u => marks,u => chase(f,heap,H.load_word(heap,p,0),W.write(marks,U32.shrn(p,2n),1)))

def free_marks(heads: List<&2,U32>, +heap: H.Heap, marks: W.Store) -> W.Store:
  match heads:
    case Nil{}: marks
    case Con{p,rest}: free_marks(rest,heap,chase(U32.to_nat(H.memory_words()),heap,p,marks))

def bump_of(heap: H.Heap) -> U32:
  match heap:
    case H.Heap{memory,bump,free}: bump

def free_of(heap: H.Heap) -> List<&2,U32>:
  match heap:
    case H.Heap{memory,bump,free}: free

# Cells from `q` to the bump pointer, skipping free cells; a block size below
# four words means the heap is corrupt and ends the walk.
def blocks(fuel: Nat, +heap: H.Heap, +marks: W.Store, +q: U32, +bump: U32, +found: List<&2,U32>) -> List<&2,U32>:
  match fuel:
    case 0n: found
    case 1n+f:
      +memory = H.memory_of(heap)
      +size = W.choose(U32,U32.is_eq(W.read(marks,q),1),u => W.read(memory,U32.add(q,1)),
        u => U32.shln(4,U32.to_nat(H.class_of(U32.add(2,U32.shrn(W.read(memory,U32.add(q,1)),3n))))))
      W.choose(List<&2,U32>,W.or(U32.is_ge(q,bump),U32.is_lt(size,4)),u => found,u =>
        blocks(f,heap,marks,U32.add(q,size),bump,Bool.pick(List<&2,U32>,U32.is_eq(W.read(marks,q),1),found,Con{U32.shln(q,2n),found})))

def live_cells(+heap: H.Heap, +base: U32) -> List<&2,U32>:
  blocks(U32.to_nat(H.memory_words()),heap,free_marks(free_of(heap),heap,W.empty()),base,bump_of(heap),Nil{})

def mortal_cells(cells: List<&2,U32>, +heap: H.Heap) -> List<&2,U32>:
  match cells:
    case Nil{}: Nil{}
    case Con{+c,+rest}: W.choose(List<&2,U32>,H.mortal(heap,c),u => Con{c,mortal_cells(rest,heap)},u => mortal_cells(rest,heap))

def all_edges(cells: List<&2,U32>, +heap: H.Heap) -> List<&2,U32>:
  match cells:
    case Nil{}: Nil{}
    case Con{c,rest}: List.append(&2,U32,H.edges(heap,c),all_edges(rest,heap))

def frame_roots(frames: List<&2,H.Frame>) -> List<&2,U32>:
  match frames:
    case Nil{}: Nil{}
    case Con{H.Gather{node,need,got},rest}: List.append(&2,U32,got,frame_roots(rest))
    case Con{H.Call{caller},rest}: Con{caller,frame_roots(rest)}
    case Con{H.InvokeArgument{node,f},rest}: Con{f,frame_roots(rest)}
    case Con{frame,rest}: frame_roots(rest)

def control_roots(control: M.Control) -> List<&2,U32>:
  match control:
    case M.Return{w}: [w]
    case M.Enter{M.Held{w},ops}: Con{w,ops}
    case M.Enter{M.Callee{f},ops}: ops
    case M.Finished{M.Answered{w}}: [w]
    case M.Finished{M.Stopped{stop,pending}}: control_roots(pending)
    case _: Nil{}

# Every owner of a reference: the result register, pending operands, the
# current Activation and every frame value (SPEC §6).
def roots(m: M.Machine) -> List<&2,U32>:
  match m:
    case M.Machine{control,H.Stack{act,frames,top},heap,meter,out}: Con{act,List.append(&2,U32,control_roots(control),frame_roots(frames))}

def tallied(words: List<&2,U32>, +heap: H.Heap, +counts: W.Store) -> W.Store:
  match words:
    case Nil{}: counts
    case Con{+w,rest}:
      tallied(rest,heap,W.choose(W.Store,H.mortal(heap,w),u => W.write(counts,U32.shrn(w,2n),U32.add(W.read(counts,U32.shrn(w,2n)),1)),u => counts))

def mortal_words(words: List<&2,U32>, +heap: H.Heap) -> U32:
  match words:
    case Nil{}: 0
    case Con{+w,rest}: U32.add(Bool.pick(U32,H.mortal(heap,w),1,0),mortal_words(rest,heap))

def matched(cells: List<&2,U32>, +heap: H.Heap, +counts: W.Store) -> Bool:
  match cells:
    case Nil{}: True{}
    case Con{+c,rest}: Bool.and(U32.is_eq(H.rc_of(heap,c),W.read(counts,U32.shrn(c,2n))),matched(rest,heap,counts))

def counted_total(cells: List<&2,U32>, +counts: W.Store) -> U32:
  match cells:
    case Nil{}: 0
    case Con{+c,rest}: U32.add(W.read(counts,U32.shrn(c,2n)),counted_total(rest,counts))

def heap_of(m: M.Machine) -> H.Heap:
  match m:
    case M.Machine{control,stack,heap,meter,out}: heap

def base_of(+code: H.Code) -> U32:
  H.heap_base(H.code_word(code,2))

# An Activation's slots at and above its depth hold 0 (SPEC §5).
def vacant(cells: List<&2,U32>, +heap: H.Heap) -> Bool:
  match cells:
    case Nil{}: True{}
    case Con{+c,rest}:
      +depth = H.load_word(heap,c,3)
      +capacity = U32.sub(U32.shrn(H.load_word(heap,c,1),3n),2)
      Bool.and(W.choose(Bool,W.or(Bool.not(U32.is_eq(H.cell_class(heap,c),4)),U32.is_gt(depth,capacity)),u => True{},
          u => W.zero_all(W.slice(U32.to_nat(U32.sub(capacity,depth)),H.memory_of(heap),U32.add(U32.shrn(c,2n),U32.add(4,depth))))),
        vacant(rest,heap))

# The RC audit: each live mortal cell's count equals its owners among the
# roots and every live cell's edges, no owner points outside them, and no
# Activation holds a word above its depth.
def balanced(+code: H.Code, +m: M.Machine) -> Bool:
  +heap = heap_of(m)
  +cells = live_cells(heap,base_of(code))
  +owners = List.append(&2,U32,roots(m),all_edges(cells,heap))
  +counts = tallied(owners,heap,W.empty())
  +mortals = mortal_cells(cells,heap)
  Bool.and(Bool.and(matched(mortals,heap,counts),U32.is_eq(counted_total(mortals,counts),mortal_words(owners,heap))),vacant(cells,heap))

# Mortal cells still live; zero once a finished run has released its answer.
def leaked(+code: H.Code, +m: M.Machine) -> U32:
  W.count(U32,mortal_cells(live_cells(heap_of(m),base_of(code)),heap_of(m)))

# SPEC §6, the atomic-stops ruling: a step that stops the machine changes no state. The stopped
# machine keeps the frames, `act`, `top`, allocation state and output of the machine that stopped;
# only an Enter's debit stands (SPEC §7).
def same_frame(a: H.Frame, b: H.Frame) -> Bool:
  match a b:
    case H.Top{p} H.Top{q}: U32.is_eq(p,q)
    case H.Gather{n,d,g} H.Gather{m,e,h}: Bool.and(Bool.and(U32.is_eq(n,m),U32.is_eq(d,e)),W.same(g,h))
    case H.Bind{n} H.Bind{m}: U32.is_eq(n,m)
    case H.Scope{d} H.Scope{e}: U32.is_eq(d,e)
    case H.Call{c} H.Call{e}: U32.is_eq(c,e)
    case H.InvokeFunction{n} H.InvokeFunction{m}: U32.is_eq(n,m)
    case H.InvokeArgument{n,f} H.InvokeArgument{m,g}: Bool.and(U32.is_eq(n,m),U32.is_eq(f,g))
    case _ _: False{}

def same_frames(a: List<&2,H.Frame>, b: List<&2,H.Frame>) -> Bool:
  match a b:
    case Nil{} Nil{}: True{}
    case Con{x,xs} Con{y,ys}: Bool.and(same_frame(x,y),same_frames(xs,ys))
    case _ _: False{}

def same_stack(a: H.Stack, b: H.Stack) -> Bool:
  match a b:
    case H.Stack{p,f,t} H.Stack{q,g,u}: Bool.and(Bool.and(U32.is_eq(p,q),U32.is_eq(t,u)),same_frames(f,g))

def same_heap(a: H.Heap, b: H.Heap) -> Bool:
  match a b:
    case H.Heap{m,p,f} H.Heap{n,q,g}: Bool.and(U32.is_eq(p,q),W.same(f,g))

def same_meter(a: M.Meter, b: M.Meter) -> Bool:
  match a b:
    case M.Meter{f,c,q} M.Meter{g,d,r}: Bool.and(Bool.and(U32.is_eq(f,g),U32.is_eq(c,d)),U32.is_eq(q,r))

def is_enter(control: M.Control) -> Bool:
  match control:
    case M.Enter{target,ops}: True{}
    case _: False{}

# `after` is `before` advanced one step: a stop changed nothing but an Enter's meter.
def atomic(before: M.Machine, after: M.Machine) -> Bool:
  match before after:
    case M.Machine{control,stack,heap,+meter,out} M.Machine{M.Finished{M.Stopped{stop,pending}},stack2,heap2,+meter2,out2}:
      Bool.and(Bool.and(same_stack(stack,stack2),same_heap(heap,heap2)),
        Bool.and(W.or(same_meter(meter,meter2),Bool.and(is_enter(control),same_meter(M.charged(meter),meter2))),
          U32.is_eq(W.count(List<&2,U32>,out),W.count(List<&2,U32>,out2))))
    case _ _: True{}

# `prior` is the machine before the last step, which a Book's description is atomic against.
type Audit is Data:
  Audit{machine: M.Machine, steps: U32, balanced: Bool, prior: M.Machine}

# A step that stopped the machine was atomic against `prior`, and the state balances: after every
# step when `each`, else after the last alone.
def audit_from(fuel: Nat, +code: H.Code, +m: M.Machine, +steps: U32, +prior: M.Machine, +each: Bool) -> Audit:
  match fuel:
    case 0n: Audit{M.halted(m,W.Bound{"transitions"}),steps,balanced(code,m),prior}
    case 1n+f:
      +sound = Bool.and(W.choose(Bool,W.or(each,M.is_finished(m)),u => balanced(code,m),u => True{}),atomic(prior,m))
      W.choose(Audit,Bool.not(sound),u => Audit{m,steps,False{},prior},u =>
      W.choose(Audit,M.is_finished(m),u => Audit{m,steps,True{},prior},u =>
        audit_from(f,code,M.settled(M.step(code,m),m),U32.add(steps,1),m,each)))

def audit_run(fuel: Nat, +code: H.Code, +m: M.Machine, +steps: U32, +each: Bool) -> Audit:
  audit_from(fuel,code,m,steps,m,each)

# Runs like `run`, auditing before every transition and after the last.
def audited(fuel: Nat, +code: H.Code, +m: M.Machine, +steps: U32) -> Audit:
  audit_run(fuel,code,m,steps,True{})

# ---------------------------------------------------------------- law predicates

# An admitted image's entry run to its end: a Book's `main` with no ordinals,
# described and dropped, or a Program's `main`. `Bound` stops a run that
# outlives the transition budget.
type Run is Data:
  Refusal{stop: W.Stop}
  Ran{code: H.Code, machine: M.Machine, balanced: Bool}

def plan_entry(plan: W.Plan) -> U32:
  match plan:
    case W.Plan{entry,types,functions,reps}: entry

# The answer's description and drop are audited too.
def concluded_run(+code: H.Code, +prior: M.Machine, result: Result<W.Stop,M.Machine>, ok: Bool) -> Run:
  match result:
    case Fail{stop}: Refusal{stop}
    case Done{+m}: Ran{code,m,Bool.and(Bool.and(ok,atomic(prior,m)),balanced(code,m))}

def run_concluded(+code: H.Code, +t: U32, a: Audit) -> Run:
  match a:
    case Audit{m,steps,ok,prior}: concluded_run(code,prior,M.concluded(code,t,m),ok)

def started_run(+code: H.Code, +t: U32, +steps: Nat, result: Result<W.Stop,M.Machine>, +each: Bool) -> Run:
  match result:
    case Fail{stop}: Refusal{stop}
    case Done{m}: run_concluded(code,t,audit_run(steps,code,m,0,each))

def ran(+plan: W.Plan, +steps: Nat, +fuel: U32, booted: Result<W.Stop,M.Booted>, +each: Bool) -> Run:
  match booted:
    case Fail{stop}: Refusal{stop}
    case Done{+b}:
      +code = M.code_of(b)
      W.choose(Run,U32.is_eq(plan_entry(plan),1),
        u => run_concluded(code,W.none(),audit_run(steps,code,M.program(plan,b,fuel),0,each)),
        u => started_run(code,M.result_type(plan,D.main_bytes()),steps,M.book(plan,b,D.main_bytes(),fuel,Nil{}),each))

def admitted_run(result: Result<W.Stop,W.Plan>, +words: List<&2,U32>, +steps: Nat, +fuel: U32, +each: Bool) -> Run:
  match result:
    case Fail{stop}: Refusal{stop}
    case Done{+plan}: ran(plan,steps,fuel,M.boot(words),each)

def run_words(+words: List<&2,U32>, +steps: Nat, +fuel: U32) -> Run:
  admitted_run(E.admit(words),words,steps,fuel,True{})

# The same run, balanced after its last step alone: cheaper, for the laws that read an outcome.
def run_words_final(+words: List<&2,U32>, +steps: Nat, +fuel: U32) -> Run:
  admitted_run(E.admit(words),words,steps,fuel,False{})

def internal(outcome: M.Outcome) -> Bool:
  match outcome:
    case M.Stopped{W.Internal{c},p}: True{}
    case M.Stopped{W.Bound{c},p}: True{}
    case _: False{}

def finished_outcome(m: M.Machine) -> M.Outcome:
  match m:
    case M.Machine{M.Finished{o},stack,heap,meter,out}: o
    case _: M.Stopped{W.Internal{"unfinished"},M.Eval{0}}

def completing(outcome: M.Outcome) -> Bool:
  match outcome:
    case M.Described{t,tag,tree}: True{}
    case M.Emitted{}: True{}
    case M.Died{c,msg}: True{}
    case _: False{}

# Validator soundness: an image is refused, or its run never meets a state the
# machine's invariants exclude, keeps every count balanced and, when it
# completes, leaves no mortal cell live.
def sound(run: Run) -> Bool:
  match run:
    case Refusal{stop}: Bool.not(internal(M.Stopped{stop,M.Eval{0}}))
    case Ran{+code,+m,balanced}:
      Bool.and(Bool.and(Bool.not(internal(finished_outcome(m))),balanced),
        W.or(Bool.not(completing(finished_outcome(m))),U32.is_eq(leaked(code,m),0)))

def balanced_run(run: Run) -> Bool:
  match run:
    case Refusal{stop}: False{}
    case Ran{code,m,balanced}: balanced

def leak_of(run: Run) -> U32:
  match run:
    case Refusal{stop}: W.none()
    case Ran{+code,+m,balanced}: leaked(code,m)

def outcome_of(run: Run) -> M.Outcome:
  match run:
    case Refusal{stop}: M.Stopped{stop,M.Eval{0}}
    case Ran{code,m,balanced}: finished_outcome(m)

# What a run's final machine still holds: its frames by SPEC §6's kind numbers, newest first,
# whether an Activation is current, and the words the frames occupy.
type Held is Data:
  Held{frames: List<&2,U32>, act: Bool, top: U32}

def frame_kind(frame: H.Frame) -> U32:
  match frame:
    case H.Top{p}: 0
    case H.Gather{n,d,g}: 1
    case H.Bind{n}: 2
    case H.Scope{d}: 3
    case H.Call{c}: 4
    case H.InvokeFunction{n}: 5
    case H.InvokeArgument{n,f}: 6

def frame_kinds(frames: List<&2,H.Frame>) -> List<&2,U32>:
  match frames:
    case Nil{}: Nil{}
    case Con{frame,rest}: Con{frame_kind(frame),frame_kinds(rest)}

def held_by(m: M.Machine) -> Held:
  match m:
    case M.Machine{control,H.Stack{act,frames,top},heap,meter,out}: Held{frame_kinds(frames),Bool.not(U32.is_eq(act,0)),top}

def held_of(run: Run) -> Held:
  match run:
    case Refusal{stop}: Held{Nil{},False{},0}
    case Ran{code,m,balanced}: held_by(m)

# Single-word mutations of an image: at each position, zero and the successor
# and predecessor of the word there (so none where the word is zero).
def mutations(n: Nat, +words: List<&2,U32>, +i: U32) -> List<&2,List<&2,U32>>:
  match n:
    case 0n: Nil{}
    case 1n+m:
      +w = W.nth(words,i)
      Con{H.replaced(words,i,0),Con{H.replaced(words,i,U32.add(w,1)),Con{H.replaced(words,i,U32.sub(w,1)),mutations(m,words,U32.add(i,1))}}}

def all_sound(images: List<&2,List<&2,U32>>, +steps: Nat, +fuel: U32) -> Bool:
  match images:
    case Nil{}: True{}
    case Con{+w,rest}: Bool.and(sound(run_words(w,steps,fuel)),all_sound(rest,steps,fuel))
