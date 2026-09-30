import Base
import ./word.bend as W
import ./decode.bend as D
import ./validate.bend as V
import ./encode.bend as E
import ./memory.bend as H

# ---------------------------------------------------------------- the machine

type Target is Data:
  Callee{function: U32}
  Held{word: U32}

# A Book halts Answered, its `act` still current, then is Described: its description is the rest of
# Return to Top(0), which drops `act` only once the description has passed. A Program Emits or Dies. A stop
# keeps the control it could not advance, whose words stay owned (SPEC §7:
# the pending Enter stays in the state).
type Outcome is Data:
  Answered{word: U32}
  Described{result: U32, tag: U32, tree: List<&2,U32>}
  Emitted{}
  Died{code: U32, message: List<&2,U32>}
  Stopped{stop: W.Stop, pending: Control}

type Control is Data:
  Eval{node: U32}
  Return{word: U32}
  Enter{target: Target, ops: List<&2,U32>}
  Finished{outcome: Outcome}

type Meter is Data:
  Meter{fuel: U32, calls: U32, quantum: U32}

# `out` holds the printed lines, newest first.
type Machine is Data:
  Machine{control: Control, stack: H.Stack, heap: H.Heap, meter: Meter, out: List<&2,List<&2,U32>>}

# A frame transition's control, frames and heap; fuel and output change only at an Enter and at Top's loop.
type Next is Data:
  Next{control: Control, stack: H.Stack, heap: H.Heap}

def to(control: Control, stack: H.Stack, heap: H.Heap) -> Result<W.Stop,Next>:
  Done{Next{control,stack,heap}}

def then_stack(-B: Data, result: Result<W.Stop,H.Stack>, next: H.Stack -> Result<W.Stop,B>) -> Result<W.Stop,B>:
  H.bind(H.Stack,B,result,next)

def operands_of(+code: H.Code, +node: U32, n: Nat, +i: U32) -> List<&2,U32>:
  match n:
    case 0n: Nil{}
    case 1n+m: Con{H.operand(code,node,i),operands_of(code,node,m,U32.add(i,1))}

def slots_of(+heap: H.Heap, +act: U32, words: List<&2,U32>) -> List<&2,U32>:
  match words:
    case Nil{}: Nil{}
    case Con{i,rest}: Con{H.slot(heap,act,i),slots_of(heap,act,rest)}

# Completing a gathered node (SPEC §6): Nat Succ and Char Chr act on the word
# they read, inspected at their own type whether or not the result is used (as
# the reference evaluation reads it); other constructors allocate an Object,
# prims compute then drop what they did not move, a Foreign builds an inert
# Action, an Application enters its callee.
def completed(+code: H.Code, +node: U32, +ops: List<&2,U32>, +stack: H.Stack, +heap: H.Heap) -> Result<W.Stop,Next>:
  +t = H.node_type(code,node)
  +id = H.operand(code,node,0)
  +a = W.nth(ops,0)
  W.choose(Result<W.Stop,Next>,U32.is_eq(H.code_word(code,U32.add(node,1)),6),u => to(Enter{Callee{id},ops},stack,heap),u =>
  W.choose(Result<W.Stop,Next>,U32.is_eq(H.code_word(code,U32.add(node,1)),12),u => H.with_cell(Next,H.alloc(heap,3,Con{id,ops}),heap => w => to(Return{w},stack,heap)),u =>
  W.choose(Result<W.Stop,Next>,U32.is_eq(H.code_word(code,U32.add(node,1)),1),
    u => H.operands_read(Next,code,heap,ops,H.primitive_inputs(V.primitive_at(V.prims(),id)),u =>
           H.with_cell(Next,H.compute(id,code,heap,a,W.nth(ops,1)),heap => w =>
             H.bind(H.Heap,Next,H.drops(H.dropped_operands(id,ops,0),heap,H.room(stack)),heap => to(Return{w},stack,heap)))),u =>
  W.choose(Result<W.Stop,Next>,H.is_rep(code,t,0),
    u => H.inspected_at(Next,code,heap,t,a,u =>
           W.choose(Result<W.Stop,Next>,U32.is_eq(H.scalar(heap,a),W.none()),u => Fail{W.Exhausted{2,"NatRange"}},u =>
             H.with_cell(Next,H.word_of(heap,U32.add(H.scalar(heap,a),1)),heap => w =>
               H.bind(H.Heap,Next,H.drop(heap,H.room(stack),a),heap => to(Return{w},stack,heap))))),u =>
  W.choose(Result<W.Stop,Next>,H.is_rep(code,t,2),u => H.inspected_at(Next,code,heap,t,a,u => to(Return{a},stack,heap)),u =>
    H.with_cell(Next,H.alloc(heap,0,Con{t,Con{id,ops}}),heap => w => to(Return{w},stack,heap)))))))

def gathered(+code: H.Code, +node: U32, +stack: H.Stack, +heap: H.Heap) -> Result<W.Stop,Next>:
  +n = H.operand(code,node,1)
  W.choose(Result<W.Stop,Next>,U32.is_eq(n,0),u => completed(code,node,Nil{},stack,heap),u =>
    then_stack(Next,H.pushed(stack,H.Gather{node,n,Nil{}}),stack => to(Eval{H.operand(code,node,2)},stack,heap)))

# §6.1: the matching row, the key's arm, or else the default.
def row_arm(+code: H.Code, +node: U32, +tag: U32) -> U32:
  +arm = W.choose(U32,U32.is_lt(tag,H.operand(code,node,3)),u => H.operand(code,node,U32.add(4,tag)),u => W.none())
  W.choose(U32,W.is_none(arm),u => H.node_last(code,node),u => arm)

def key_arm(n: Nat, +code: H.Code, +node: U32, +v: U32, +i: U32) -> U32:
  match n:
    case 0n: H.node_last(code,node)
    case 1n+m:
      W.choose(U32,U32.is_eq(H.operand(code,node,U32.add(4,U32.mul(2,i))),v),u => H.operand(code,node,U32.add(5,U32.mul(2,i))),u =>
        key_arm(m,code,node,v,U32.add(i,1)))

type Fields is Data:
  Fields{heap: H.Heap, words: List<&2,U32>}

def with_fields(-B: Data, result: Result<W.Stop,Fields>, next: H.Heap -> List<&2,U32> -> Result<W.Stop,B>) -> Result<W.Stop,B>:
  match result:
    case Fail{stop}: Fail{stop}
    case Done{Fields{heap,words}}: next(heap,words)

# Words a selected Branch binds: a Nat's predecessor is a new word, a Char
# binds its own code word, an Object its fields; each slot owns a reference.
def selected_fields(+code: H.Code, +heap: H.Heap, +t: U32, +w: U32, +f: U32) -> Result<W.Stop,Fields>:
  +fields = W.slice(U32.to_nat(f),H.memory_of(heap),U32.add(U32.shrn(w,2n),4))
  W.choose(Result<W.Stop,Fields>,H.is_rep(code,t,0),u => H.with_cell(Fields,H.word_of(heap,U32.sub(H.scalar(heap,w),1)),heap => x => Done{Fields{heap,[x]}}),u =>
  W.choose(Result<W.Stop,Fields>,H.is_rep(code,t,2),u => H.bind(H.Heap,Fields,H.dup(heap,w),heap => Done{Fields{heap,[w]}}),u =>
    H.bind(H.Heap,Fields,H.dups(fields,heap),heap => Done{Fields{heap,fields}})))

# A Branch binding f fields enters its body in a new Scope, pushed before its
# fields are made (§6.1: the frame region is exhausted before the heap).
def branch_entered(+code: H.Code, +arm: U32, +f: U32, +t: U32, +w: U32, +stack: H.Stack, +heap: H.Heap) -> Result<W.Stop,Next>:
  +act = H.act_of(stack)
  W.choose(Result<W.Stop,Next>,U32.is_eq(f,0),u => to(Eval{H.operand(code,arm,3)},stack,heap),
    u => then_stack(Next,H.pushed(stack,H.Scope{H.depth_of(heap,act)}),stack =>
           with_fields(Next,selected_fields(code,heap,t,w,f),+heap => words =>
             to(Eval{H.operand(code,arm,3)},stack,H.deepened(H.binds(words,heap,act,H.depth_of(heap,act)),act,U32.add(H.depth_of(heap,act),f))))))

# The selected arm is a Default or a Branch. An absent arm (`none`) or any
# other record means the validator admitted a Case it should not have: the
# machine stops as Internal instead of reading a wrapped offset.
def entered_arm(+code: H.Code, +arm: U32, +t: U32, +w: U32, +stack: H.Stack, +heap: H.Heap) -> Result<W.Stop,Next>:
  +op = W.choose(U32,W.is_none(arm),u => W.none(),u => H.code_word(code,U32.add(arm,1)))
  W.choose(Result<W.Stop,Next>,U32.is_eq(op,2),u => to(Eval{H.operand(code,arm,0)},stack,heap),u =>
  W.choose(Result<W.Stop,Next>,U32.is_eq(op,9),u => branch_entered(code,arm,H.operand(code,arm,2),t,w,stack,heap),u =>
    Fail{W.Internal{"case arm"}}))

# D24: a request matches no row, in either mode, so the Default takes it unread and binds nothing;
# a Case without a Default refuses it (SPEC §6.1).
def defaulted(+code: H.Code, +node: U32, +t: U32, +w: U32, +stack: H.Stack, +heap: H.Heap) -> Result<W.Stop,Next>:
  +arm = H.node_last(code,node)
  W.choose(Result<W.Stop,Next>,W.is_none(arm),u => H.unsupported(Next),u => entered_arm(code,arm,t,w,stack,heap))

def selected(+code: H.Code, +node: U32, +stack: H.Stack, +heap: H.Heap) -> Result<W.Stop,Next>:
  +t = H.operand(code,node,1)
  +w = H.slot(heap,H.act_of(stack),H.operand(code,node,0))
  W.choose(Result<W.Stop,Next>,H.is_request(heap,w),u => defaulted(code,node,t,w,stack,heap),u =>
  H.inspected_at(Next,code,heap,t,w,u =>
    entered_arm(code,W.choose(U32,U32.is_eq(H.operand(code,node,2),0),
      u => row_arm(code,node,H.tag_of(code,heap,t,w)),
      u => key_arm(U32.to_nat(H.operand(code,node,3)),code,node,H.scalar(heap,w),0)),t,w,stack,heap)))

def closed(+code: H.Code, +node: U32, +stack: H.Stack, +heap: H.Heap) -> Result<W.Stop,Next>:
  +captured = slots_of(heap,H.act_of(stack),operands_of(code,node,U32.to_nat(H.operand(code,node,3)),4))
  H.bind(H.Heap,Next,H.dups(captured,heap),heap =>
    H.with_cell(Next,H.alloc(heap,1,Con{node,captured}),heap => w => to(Return{w},stack,heap)))

def evaluated(op: Nat, +code: H.Code, +node: U32, +stack: H.Stack, +heap: H.Heap) -> Result<W.Stop,Next>:
  match op:
    case 0n: to(Return{H.pool_word(code,H.operand(code,node,0))},stack,heap)
    case 3n: to(Return{H.immediate(H.operand(code,node,0))},stack,heap)
    case 5n:
      +w = H.slot(heap,H.act_of(stack),H.operand(code,node,0))
      H.bind(H.Heap,Next,H.dup(heap,w),heap => to(Return{w},stack,heap))
    case 1n: gathered(code,node,stack,heap)
    case 4n: gathered(code,node,stack,heap)
    case 6n: gathered(code,node,stack,heap)
    case 12n: gathered(code,node,stack,heap)
    case 7n: then_stack(Next,H.pushed(stack,H.Bind{node}),stack => to(Eval{H.operand(code,node,1)},stack,heap))
    case 8n: selected(code,node,stack,heap)
    case 10n: closed(code,node,stack,heap)
    case 11n: then_stack(Next,H.pushed(stack,H.InvokeFunction{node}),stack => to(Eval{H.operand(code,node,0)},stack,heap))
    case _: Fail{W.Internal{"eval arm"}}

def unwound(n: Nat, +heap: H.Heap, +act: U32, +i: U32, +room: U32) -> Result<W.Stop,H.Heap>:
  match n:
    case 0n: Done{heap}
    case 1n+m: H.bind(H.Heap,H.Heap,H.drop(heap,room,H.slot(heap,act,i)),heap => unwound(m,H.bound(heap,act,i,0),act,U32.sub(i,1),room))

def is_scalar_text(codes: List<&2,U32>) -> Bool:
  match codes:
    case Nil{}: True{}
    case Con{+c,rest}: Bool.and(Bool.and(U32.is_le(c,1114111),Bool.not(W.within(c,55296,57343))),is_scalar_text(rest))

# An outgoing String (SPEC §10, D20): read whole, and refused before any host call if a Char is not a Unicode scalar.
def outgoing(+code: H.Code, +heap: H.Heap, +w: U32) -> Result<W.Stop,List<&2,U32>>:
  H.bind(List<&2,U32>,List<&2,U32>,H.string_of(code,heap,w),+line =>
    W.choose(Result<W.Stop,List<&2,U32>>,Bool.not(is_scalar_text(H.scalars_of(line,heap))),u => Fail{W.Refused{"io","abi"}},u =>
      Done{H.scalars_of(line,heap)}))

def topped(+code: H.Code, +phase: U32, +w: U32, +rest: List<&2,H.Frame>, +top: U32, +heap: H.Heap) -> Result<W.Stop,Next>:
  W.choose(Result<W.Stop,Next>,U32.is_eq(phase,1),u => to(Enter{Held{w},Nil{}},H.Stack{0,Con{H.Top{2},rest},top},heap),u =>
  W.choose(Result<W.Stop,Next>,U32.is_eq(phase,2),u => to(Enter{Held{w},[H.terminal(code)]},H.Stack{0,Con{H.Top{3},rest},top},heap),u =>
    H.inspected_at(Next,code,heap,H.rep(code,10),w,u =>
      W.choose(Result<W.Stop,Next>,U32.is_eq(H.load_word(heap,w,3),0),
        u => H.bind(H.Heap,Next,H.drop(heap,H.room(H.Stack{0,rest,top}),w),heap => to(Finished{Emitted{}},H.Stack{0,Con{H.Top{3},rest},top},heap)),
        u => H.inspected_at(Next,code,heap,H.rep(code,1),H.load_word(heap,w,4),u =>
               H.bind(List<&2,U32>,Next,outgoing(code,heap,H.load_word(heap,w,5)),message =>
               H.bind(H.Heap,Next,H.drop(heap,H.room(H.Stack{0,rest,top}),w),heap2 =>
                 to(Finished{Died{H.scalar(heap,H.load_word(heap,w,4)),message}},H.Stack{0,Con{H.Top{3},rest},top},heap2))))))))

# The Return transitions of SPEC §6, by the top frame. A Book's Top(0) keeps `act` for `concluded`.
def returned(+code: H.Code, +w: U32, +stack: H.Stack, +heap: H.Heap) -> Result<W.Stop,Next>:
  match stack:
    case H.Stack{+act,Con{H.Gather{+node,+need,+got},+rest},+top}:
      +have : List<&2,U32> = Con{w,got}
      W.choose(Result<W.Stop,Next>,U32.is_lt(W.count(U32,have),need),
        u => to(Eval{H.operand(code,node,U32.add(2,W.count(U32,have)))},H.Stack{act,Con{H.Gather{node,need,have},rest},top},heap),
        u => completed(code,node,List.reverse(&2,U32,have),H.Stack{act,rest,U32.sub(top,U32.add(need,3))},heap))
    case H.Stack{+act,Con{H.Bind{+node},rest},+top}:
      +d = H.depth_of(heap,act)
      then_stack(Next,H.pushed(H.Stack{act,rest,U32.sub(top,3)},H.Scope{d}),stack =>
        to(Eval{H.operand(code,node,2)},stack,H.deepened(H.bound(heap,act,d,w),act,U32.add(d,1))))
    case H.Stack{+act,Con{H.Scope{+saved},rest},+top}:
      +popped : H.Stack = H.Stack{act,rest,U32.sub(top,3)}
      +d = H.depth_of(heap,act)
      H.bind(H.Heap,Next,unwound(U32.to_nat(U32.sub(d,saved)),heap,act,U32.sub(d,1),H.room(popped)),heap =>
        to(Return{w},popped,H.deepened(heap,act,saved)))
    case H.Stack{+act,Con{H.Call{+caller},rest},+top}:
      +popped : H.Stack = H.Stack{act,rest,U32.sub(top,4)}
      H.bind(H.Heap,Next,H.drop(heap,H.room(popped),act),heap => to(Return{w},H.with_act(popped,caller),heap))
    case H.Stack{+act,Con{H.InvokeFunction{+node},rest},+top}:
      +popped : H.Stack = H.Stack{act,rest,U32.sub(top,3)}
      W.choose(Result<W.Stop,Next>,U32.is_eq(H.operand(code,node,1),1),
        u => then_stack(Next,H.pushed(popped,H.InvokeArgument{node,w}),stack => to(Eval{H.operand(code,node,2)},stack,heap)),
        u => to(Enter{Held{w},Nil{}},popped,heap))
    case H.Stack{+act,Con{H.InvokeArgument{node,+f},rest},+top}:
      to(Enter{Held{f},[w]},H.Stack{act,rest,U32.sub(top,4)},heap)
    case H.Stack{act,Con{H.Top{0},rest},top}: to(Finished{Answered{w}},stack,heap)
    case H.Stack{+act,Con{H.Top{+phase},+rest},+top}:
      H.bind(H.Heap,Next,H.drop(heap,H.room(H.Stack{act,rest,top}),act),heap => topped(code,phase,w,rest,top,heap))
    case H.Stack{act,Nil{},top}: Fail{W.Internal{"no frame"}}

# §6.2: an entry is in tail position when only Scope frames separate it from
# the nearest Call or Top frame.
def tail(frames: List<&2,H.Frame>) -> Bool:
  match frames:
    case Con{H.Scope{d},rest}: tail(rest)
    case Con{H.Call{c},rest}: True{}
    case Con{H.Top{p},rest}: True{}
    case _: False{}

def unscoped_frames(frames: List<&2,H.Frame>, +act: U32, +top: U32) -> H.Stack:
  match frames:
    case Con{H.Scope{d},rest}: unscoped_frames(rest,act,U32.sub(top,3))
    case _: H.Stack{act,frames,top}

def unscoped(stack: H.Stack) -> H.Stack:
  match stack:
    case H.Stack{act,frames,top}: unscoped_frames(frames,act,top)

def frames_of(stack: H.Stack) -> List<&2,H.Frame>:
  match stack:
    case H.Stack{act,frames,top}: frames

def called(+stack: H.Stack, +heap: H.Heap) -> Result<W.Stop,Next>:
  W.choose(Result<W.Stop,Next>,tail(frames_of(stack)),
    u => H.bind(H.Heap,Next,H.drop(heap,H.room(unscoped(stack)),H.act_of(stack)),heap => to(Eval{0},H.with_act(unscoped(stack),0),heap)),
    u => then_stack(Next,H.pushed(stack,H.Call{H.act_of(stack)}),stack => to(Eval{0},H.with_act(stack,0),heap)))

def with_next(-B: Data, result: Result<W.Stop,Next>, next: H.Stack -> H.Heap -> Result<W.Stop,B>) -> Result<W.Stop,B>:
  match result:
    case Fail{stop}: Fail{stop}
    case Done{Next{control,stack,heap}}: next(stack,heap)

# Entering a body (SPEC §7): tail entries release the caller first, others
# push Call; then a fresh Activation holds the bound slots. A closure's
# captures gain references and the closure itself is dropped last.
def body_entered(+code: H.Code, +owner: U32, +capacity: U32, +depth: U32, +words: List<&2,U32>, +body: U32, +captures: List<&2,U32>, +closure: U32, +stack: H.Stack, +heap: H.Heap) -> Result<W.Stop,Next>:
  with_next(Next,called(stack,heap),+stack => heap =>
    H.with_cell(Next,H.alloc(heap,4,Con{owner,Con{depth,List.append(&2,U32,words,H.zeros(U32.to_nat(U32.sub(capacity,W.count(U32,words)))))}}),heap => a =>
      H.bind(H.Heap,Next,H.dups(captures,heap),heap =>
        H.bind(H.Heap,Next,H.drop(heap,H.room(stack),closure),heap => to(Eval{body},H.with_act(stack,a),heap)))))

def machine_of(result: Result<W.Stop,Next>, meter: Meter, out: List<&2,List<&2,U32>>) -> Result<W.Stop,Machine>:
  match result:
    case Fail{stop}: Fail{stop}
    case Done{Next{control,stack,heap}}: Done{Machine{control,stack,heap,meter,out}}

def charged(meter: Meter) -> Meter:
  match meter:
    case Meter{fuel,calls,+quantum}:
      Meter{U32.sub(fuel,1),U32.add(calls,1),Bool.pick(U32,U32.is_eq(U32.add(quantum,1),65536),0,U32.add(quantum,1))}

def fuel_of(meter: Meter) -> U32:
  match meter:
    case Meter{fuel,calls,quantum}: fuel

# §7 step 1: the target is a function, a Closure cell (the terminal
# continuation is one with node none), or an Action cell, applied to as many
# words as its arrow is live.
def admissible(+code: H.Code, +heap: H.Heap, target: Target, +ops: List<&2,U32>) -> Bool:
  match target:
    case Callee{f}: True{}
    case Held{+w}:
      +class = H.cell_class(heap,w)
      +node = H.load_word(heap,w,2)
      Bool.and(H.is_pointer(w),
        W.choose(Bool,U32.is_eq(class,3),u => U32.is_le(W.count(U32,ops),1),u =>
        W.choose(Bool,U32.is_eq(class,1),
          u => U32.is_eq(W.count(U32,ops),W.choose(U32,W.is_none(node),u => 1,u => H.operand(code,node,1))),
          u => False{})))

# The effect of `w`, an Action or a Request (each holds `foreign, operand…`), then `k` entered with the
# result (SPEC §8, §10): the operand is read whole and D20-checked before the host writes.
# Only IO.print is modelled; another foreign is refused, never faked.
def performed(+code: H.Code, +w: U32, +k: U32, +stack: H.Stack, +heap: H.Heap, meter: Meter, out: List<&2,List<&2,U32>>) -> Result<W.Stop,Machine>:
  W.choose(Result<W.Stop,Machine>,Bool.not(U32.is_eq(H.load_word(heap,w,2),1)),
    u => Fail{W.Unsupported{"vm",String.append("foreign ",U32.show(H.load_word(heap,w,2)))}},
    u => H.bind(List<&2,U32>,Machine,outgoing(code,heap,H.load_word(heap,w,3)),line =>
      H.bind(H.Heap,Machine,H.drop(heap,H.room(stack),w),heap =>
        Done{Machine{Enter{Held{k},[H.immediate(0)]},stack,heap,meter,Con{line,out}}})))

# Enter(Action, [k]) builds a Request (SPEC §7, D23): the Action's foreign word and duplicated
# operands, then `k`, whose reference moves in. Nothing is read or performed.
def requested(+w: U32, +k: U32, +stack: H.Stack, +heap: H.Heap, meter: Meter, out: List<&2,List<&2,U32>>) -> Result<W.Stop,Machine>:
  +operands = H.edges(heap,w)
  H.bind(H.Heap,Machine,H.dups(operands,heap),+heap =>
    H.with_cell(Machine,H.alloc(heap,5,Con{H.load_word(heap,w,2),List.append(&2,U32,operands,[k])}),heap => r =>
      H.bind(H.Heap,Machine,H.drop(heap,H.room(stack),w),heap => Done{Machine{Return{r},stack,heap,meter,out}})))

def held_entered(+code: H.Code, +w: U32, +ops: List<&2,U32>, +stack: H.Stack, +heap: H.Heap, +meter: Meter, +out: List<&2,List<&2,U32>>) -> Result<W.Stop,Machine>:
  +node = H.load_word(heap,w,2)
  +captures = W.slice(U32.to_nat(U32.sub(U32.shrn(H.load_word(heap,w,1),3n),1)),H.memory_of(heap),U32.add(U32.shrn(w,2n),3))
  W.choose(Result<W.Stop,Machine>,U32.is_eq(H.cell_class(heap,w),3),
    u => W.choose(Result<W.Stop,Machine>,U32.is_eq(W.count(U32,ops),0),
      u => Done{Machine{Return{w},stack,heap,meter,out}},
      u => requested(w,W.nth(ops,0),stack,heap,meter,out)),
    u => W.choose(Result<W.Stop,Machine>,W.is_none(node),
      u => machine_of(H.with_cell(Next,H.alloc(heap,0,[H.rep(code,10),0,W.nth(ops,0)]),heap => e => to(Return{e},stack,heap)),meter,out),
      u => machine_of(body_entered(code,node,H.operand(code,node,2),U32.add(W.count(U32,captures),W.count(U32,ops)),
             List.append(&2,U32,captures,ops),H.node_last(code,node),captures,w,stack,heap),meter,out)))

def target_entered(+code: H.Code, target: Target, +ops: List<&2,U32>, +stack: H.Stack, +heap: H.Heap, meter: Meter, out: List<&2,List<&2,U32>>) -> Result<W.Stop,Machine>:
  match target:
    case Callee{+f}:
      +record = H.function_record(code,f)
      +body = H.code_word(code,U32.add(record,5))
      machine_of(body_entered(code,body,H.code_word(code,U32.add(record,4)),H.code_word(code,U32.add(record,3)),ops,body,Nil{},0,stack,heap),meter,out)
    case Held{+w}: held_entered(code,w,ops,stack,heap,meter,out)

def halted(m: Machine, stop: W.Stop) -> Machine:
  match m:
    case Machine{control,stack,heap,meter,out}: Machine{Finished{Stopped{stop,control}},stack,heap,meter,out}

# A target that stops the machine after its entry was paid for keeps the debit:
# the pending Enter stays owned, but its fuel and call are spent (SPEC §7).
def paid(result: Result<W.Stop,Machine>, m: Machine) -> Result<W.Stop,Machine>:
  match result:
    case Fail{stop}: Done{halted(m,stop)}
    case Done{next}: Done{next}

def targets_request(+heap: H.Heap, target: Target) -> Bool:
  match target:
    case Callee{f}: False{}
    case Held{+w}: H.is_request(heap,w)

# Enter (SPEC §7): check the target, a request first, pay one fuel, then run the target.
def entered(+code: H.Code, +target: Target, +ops: List<&2,U32>, +stack: H.Stack, +heap: H.Heap, +meter: Meter, +out: List<&2,List<&2,U32>>) -> Result<W.Stop,Machine>:
  W.choose(Result<W.Stop,Machine>,targets_request(heap,target),u => H.unsupported(Machine),u =>
  W.choose(Result<W.Stop,Machine>,Bool.not(admissible(code,heap,target,ops)),u => H.ill_typed(Machine),u =>
  W.choose(Result<W.Stop,Machine>,U32.is_eq(fuel_of(meter),0),u => Fail{W.Exhausted{1,"fuel"}},u =>
    paid(target_entered(code,target,ops,stack,heap,charged(meter),out),Machine{Enter{target,ops},stack,heap,charged(meter),out}))))

# Top's phase 3 is a loop (SPEC §8, D23): the request that a run returns there is performed and its
# continuation entered, in one step that is no entry, with the phase unchanged. Any other Return is a frame's.
def looped(+code: H.Code, +w: U32, +stack: H.Stack, +heap: H.Heap, +meter: Meter, +out: List<&2,List<&2,U32>>) -> Result<W.Stop,Machine>:
  match stack:
    case H.Stack{+act,Con{H.Top{3},+rest},+top}:
      W.choose(Result<W.Stop,Machine>,H.is_request(heap,w),
        u => H.bind(H.Heap,Machine,H.drop(heap,H.room(H.Stack{act,rest,top}),act),+heap =>
               H.bind(H.Heap,Machine,H.dup(heap,H.continuation(heap,w)),+heap =>
                 performed(code,w,H.continuation(heap,w),H.Stack{0,Con{H.Top{3},rest},top},heap,meter,out))),
        u => machine_of(returned(code,w,stack,heap),meter,out))
    case _: machine_of(returned(code,w,stack,heap),meter,out)

def step(+code: H.Code, m: Machine) -> Result<W.Stop,Machine>:
  match m:
    case Machine{Eval{+node},stack,heap,meter,out}: machine_of(evaluated(H.node_op(code,node),code,node,stack,heap),meter,out)
    case Machine{Return{w},stack,heap,meter,out}: looped(code,w,stack,heap,meter,out)
    case Machine{Enter{target,ops},stack,heap,meter,out}: entered(code,target,ops,stack,heap,meter,out)
    case Machine{Finished{outcome},stack,heap,meter,out}: Done{Machine{Finished{outcome},stack,heap,meter,out}}

# A refused step leaves the machine as it was and records why.
def settled(result: Result<W.Stop,Machine>, m: Machine) -> Machine:
  match result:
    case Fail{stop}: halted(m,stop)
    case Done{next}: next

def is_finished(m: Machine) -> Bool:
  match m:
    case Machine{Finished{o},stack,heap,meter,out}: True{}
    case _: False{}

# The host calls made (SPEC §8's `effects`). Only IO.print is modelled, so each is one line of `out`.
def effects(m: Machine) -> U32:
  match m:
    case Machine{control,stack,heap,meter,out}: W.count(List<&2,U32>,out)

# Transitions until the machine finishes. The Nat bound is the model's own
# harness limit, reported as `Bound`, never as VM exhaustion.
def run(fuel: Nat, +code: H.Code, +m: Machine) -> Machine:
  match fuel:
    case 0n: halted(m,W.Bound{"transitions"})
    case 1n+f: W.choose(Machine,is_finished(m),u => m,u => run(f,code,settled(step(code,m),m)))

# ---------------------------------------------------------------- describing a Book result

# The describe walk's work: a word to inspect at a type, text charged by its
# bytes, and an inspected Nat word n, whose unary spelling is charged before
# it is built.
type Piece is Data:
  Shown{word: U32, result: U32}
  Said{text: List<&2,U32>}
  Unary{result: U32, n: U32}

def text(s: String) -> List<&2,U32>:
  match s:
    case SNil{}: Nil{}
    case SCon{Chr{c},rest}: Con{c,text(rest)}

def repeated_text(n: Nat, +t: List<&2,U32>) -> List<&2,U32>:
  match n:
    case 0n: Nil{}
    case 1n+m: List.append(&2,U32,t,repeated_text(m,t))

def image_of_code(code: H.Code) -> W.Store:
  match code:
    case H.Code{image,types,constructors,functions,names,pool,reps,terminal}: image

def name_codes(+code: H.Code, +n: U32) -> List<&2,U32>:
  +record = H.name_record(code,n)
  Maybe.default(&2,List<&2,U32>,W.scalars(List.take(&2,U32,W.unpack(W.slice(U32.to_nat(U32.sub(H.code_word(code,record),2)),image_of_code(code),U32.add(record,2))),U32.to_nat(H.code_word(code,U32.add(record,1))))),Nil{})

def constructor_name(+code: H.Code, +t: U32, +tag: U32) -> List<&2,U32>:
  name_codes(code,H.code_word(code,U32.add(H.constructor_record(code,t,tag),3)))

# The UTF-8 bytes of rendered text: §8 bounds the tree's bytes, not its scalars.
def text_size(t: List<&2,U32>) -> U32:
  match t:
    case Nil{}: 0
    case Con{+c,rest}:
      U32.add(W.choose(U32,U32.is_lt(c,128),u => 1,u => W.choose(U32,U32.is_lt(c,2048),u => 2,u => W.choose(U32,U32.is_lt(c,65536),u => 3,u => 4))),text_size(rest))

def field_pieces(n: Nat, +code: H.Code, +heap: H.Heap, +t: U32, +tag: U32, +w: U32, +i: U32) -> List<&2,Piece>:
  match n:
    case 0n: [Said{text("}")}]
    case 1n+m:
      Con{Said{Bool.pick(List<&2,U32>,U32.is_eq(i,0),Nil{},text(","))},Con{Shown{H.load_word(heap,w,U32.add(4,i)),H.field_type(code,t,tag,i)},
        field_pieces(m,code,heap,t,tag,w,U32.add(i,1))}}

def pieces(+code: H.Code, +heap: H.Heap, +w: U32, +t: U32) -> List<&2,Piece>:
  +tag = H.tag_of(code,heap,t,w)
  +name = constructor_name(code,t,tag)
  +fields = H.field_count(code,t,tag)
  W.choose(List<&2,Piece>,H.is_rep(code,t,0),u => [Unary{t,H.scalar(heap,w)}],u =>
  W.choose(List<&2,Piece>,U32.is_eq(fields,0),u => [Said{List.append(&2,U32,name,text("{}"))}],
    u => Con{Said{List.append(&2,U32,name,text("{"))},field_pieces(U32.to_nat(fields),code,heap,t,tag,w,0)}))

# A Nat word n spells its logical view, n Succ levels around Zero, in the
# image's own constructor names.
def unary(+code: H.Code, +t: U32, +n: U32) -> List<&2,U32>:
  List.append(&2,U32,repeated_text(U32.to_nat(n),List.append(&2,U32,constructor_name(code,t,1),text("{"))),
    List.append(&2,U32,constructor_name(code,t,0),List.append(&2,U32,text("{}"),repeated_text(U32.to_nat(n),text("}")))))

# Its bytes, n (|Succ| + 2) + |Zero| + 2, or none when they exceed `room`;
# compared by division, so nothing wraps.
def unary_size(+code: H.Code, +t: U32, +n: U32, +room: U32) -> U32:
  +level = U32.add(text_size(constructor_name(code,t,1)),2)
  +base = U32.add(text_size(constructor_name(code,t,0)),2)
  W.choose(U32,U32.is_gt(base,room),u => W.none(),u =>
  W.choose(U32,U32.is_gt(n,U32.div(U32.sub(room,base),level)),u => W.none(),u => U32.add(U32.mul(n,level),base)))

def display_limit() -> U32:
  16777216

def visit_limit() -> U32:
  1048576

def exhausted(-A: Data) -> Result<W.Stop,A>:
  Fail{W.Exhausted{2,"display"}}

# §8: an iterative walk. A visit is one rendered constructor: every shown word
# pays one, and a Nat word n its n further levels. The tree's bytes include
# its separators. Both bounds are inclusive; a word is inspected before it is
# charged, and charged before it is spelled.
def render(fuel: Nat, +code: H.Code, +heap: H.Heap, work: List<&2,Piece>, +visits: U32, +size: U32, parts: List<&2,List<&2,U32>>) -> Result<W.Stop,List<&2,U32>>:
  match fuel work:
    case _ Nil{}: Done{List.concat(&2,U32,List.reverse(&2,List<&2,U32>,parts))}
    case 0n _: Fail{W.Internal{"render fuel"}}
    case 1n+ +f Con{Said{+t},rest}:
      W.choose(Result<W.Stop,List<&2,U32>>,U32.is_gt(text_size(t),U32.sub(display_limit(),size)),u => exhausted(List<&2,U32>),u =>
        render(f,code,heap,rest,visits,U32.add(size,text_size(t)),Con{t,parts}))
    case 1n+ +f Con{Unary{+t,+n},rest}:
      W.choose(Result<W.Stop,List<&2,U32>>,U32.is_gt(n,U32.sub(visit_limit(),visits)),u => exhausted(List<&2,U32>),u =>
      W.choose(Result<W.Stop,List<&2,U32>>,W.is_none(unary_size(code,t,n,U32.sub(display_limit(),size))),u => exhausted(List<&2,U32>),u =>
        render(f,code,heap,rest,U32.add(visits,n),U32.add(size,unary_size(code,t,n,U32.sub(display_limit(),size))),Con{unary(code,t,n),parts})))
    case 1n+ +f Con{Shown{+w,+t},rest}:
      H.inspected_at(List<&2,U32>,code,heap,t,w,u =>
      W.choose(Result<W.Stop,List<&2,U32>>,U32.is_ge(visits,visit_limit()),u => exhausted(List<&2,U32>),u =>
        render(f,code,heap,List.append(&2,Piece,pieces(code,heap,w,t),rest),U32.add(visits,1),size,parts)))

def described(+code: H.Code, +heap: H.Heap, +w: U32, +t: U32) -> Result<W.Stop,List<&2,U32>>:
  render(U32.to_nat(W.none()),code,heap,[Shown{w,t}],0,0,Nil{})

# ---------------------------------------------------------------- booting

def indexed(offsets: List<&2,U32>, store: W.Store, +i: U32) -> W.Store:
  match offsets:
    case Nil{}: store
    case Con{a,rest}: indexed(rest,W.write(store,i,a),U32.add(i,1))

type Pooled is Data:
  Pooled{heap: H.Heap, pool: W.Store}

def with_pooled(-B: Data, result: Result<W.Stop,Pooled>, next: H.Heap -> W.Store -> Result<W.Stop,B>) -> Result<W.Stop,B>:
  match result:
    case Fail{stop}: Fail{stop}
    case Done{Pooled{heap,pool}}: next(heap,pool)

def immortal_scalar(+heap: H.Heap, +v: U32) -> Result<W.Stop,H.Cell>:
  W.choose(Result<W.Stop,H.Cell>,H.boxed(v),u => H.allocate(heap,W.none(),2,[v]),u => Done{H.Cell{heap,H.immediate(v)}})

# A String constant is an immortal SCon chain built from its last character,
# each boxed code in a Big cell just before the SCon holding it (SPEC §5).
def immortal_chain(last_first: List<&2,U32>, +string: U32, +heap: H.Heap, +tail: U32) -> Result<W.Stop,H.Cell>:
  match last_first:
    case Nil{}: Done{H.Cell{heap,tail}}
    case Con{c,rest}:
      H.with_cell(H.Cell,immortal_scalar(heap,c),heap => char =>
        H.with_cell(H.Cell,H.allocate(heap,W.none(),0,[string,1,char,tail]),heap => w => immortal_chain(rest,string,heap,w)))

def pooled(constants: List<&2,U32>, +image: W.Store, +string: U32, +heap: H.Heap, +pool: W.Store, +i: U32) -> Result<W.Stop,Pooled>:
  match constants:
    case Nil{}: Done{Pooled{heap,pool}}
    case Con{+a,rest}:
      H.with_cell(Pooled,W.choose(Result<W.Stop,H.Cell>,U32.is_eq(W.read(image,U32.add(a,1)),3),
          u => immortal_chain(List.reverse(&2,U32,W.slice(U32.to_nat(W.read(image,U32.add(a,2))),image,U32.add(a,3))),string,heap,H.immediate(0)),
          u => immortal_scalar(heap,W.read(image,U32.add(a,3)))),heap => w =>
        pooled(rest,image,string,heap,W.write(pool,i,w),U32.add(i,1)))

type Booted is Data:
  Booted{code: H.Code, heap: H.Heap}

def terminal_cell(+program: Bool, +heap: H.Heap) -> Result<W.Stop,H.Cell>:
  W.choose(Result<W.Stop,H.Cell>,program,u => H.allocate(heap,W.none(),1,[W.none()]),u => Done{H.Cell{heap,0}})

# Load time (SPEC §5): constants materialize in index order from the heap
# base, immortal; a Program then gets its immortal terminal continuation.
def booted_sections(lists: List<&2,List<&2,U32>>, +image: W.Store, +total: U32) -> Result<W.Stop,Booted>:
  match lists:
    case Con{t,Con{c,Con{f,Con{k,Con{n,Con{m,Nil{}}}}}}}:
      +reps = W.slice(12n,image,12)
      with_pooled(Booted,pooled(k,image,W.nth(reps,3),H.Heap{W.empty(),H.heap_base(total),H.zeros(29n)},W.empty(),0),heap => pool =>
        H.with_cell(Booted,terminal_cell(U32.is_eq(W.read(image,3),1),heap),heap => last =>
          Done{Booted{H.Code{image,indexed(t,W.empty(),0),indexed(c,W.empty(),0),indexed(f,W.empty(),0),indexed(m,W.empty(),0),pool,reps,last},heap}}))
    case _: Fail{W.Internal{"sections"}}

def boot(+words: List<&2,U32>) -> Result<W.Stop,Booted>:
  +image = W.stored(words,W.empty(),0)
  +total = W.count(U32,words)
  H.bind(List<&2,List<&2,U32>>,Booted,D.sections(List<&2,List<&2,U32>>,6n,image,total,0,32,Nil{},lists => Done{lists}),lists =>
    booted_sections(lists,image,total))

# ---------------------------------------------------------------- Books and Programs

def constructor_fields(cs: List<&2,W.Constructor>) -> List<&2,List<&2,U32>>:
  match cs:
    case Nil{}: Nil{}
    case Con{W.Constructor{name,fields},rest}: Con{fields,constructor_fields(rest)}

# §8's describe domain: algebraic, with every live field of every constructor
# describable in turn; a cycle through algebraic types stays describable.
def describable(fuel: Nat, +types: List<&2,W.Sort>, work: List<&2,U32>, +seen: List<&2,U32>) -> Bool:
  match fuel work:
    case _ Nil{}: True{}
    case 0n _: False{}
    case 1n+ +f Con{+t,+rest}:
      W.choose(Bool,W.is_none(t),u => False{},u =>
      W.choose(Bool,W.member(seen,t),u => describable(f,types,rest,seen),u =>
      W.choose(Bool,Bool.not(U32.is_eq(V.kind(types,t),0)),u => False{},u =>
        describable(f,types,List.append(&2,U32,List.concat(&2,U32,constructor_fields(V.constructors_of(types,t))),rest),Con{t,seen}))))

# §8's walk: each live parameter, left to right, takes the next ordinal, which
# must be a nullary tag of its algebraic type. An arrow takes none, and an
# opaque or `none` type has no tag. Missing and leftover ordinals are arity.
def arguments(parameters: List<&2,U32>, ordinals: List<&2,U32>, +types: List<&2,W.Sort>) -> Result<W.Stop,List<&2,U32>>:
  match parameters ordinals:
    case Nil{} Nil{}: Done{Nil{}}
    case Con{+p,ps} Con{+o,os}:
      W.choose(Result<W.Stop,List<&2,U32>>,V.is_arrow(V.kind(types,p)),u => Fail{W.Refused{"invoke","function-argument"}},u =>
      W.choose(Result<W.Stop,List<&2,U32>>,U32.is_ge(o,W.count(W.Constructor,V.constructors_of(types,p))),u => Fail{W.Refused{"invoke","argument-range"}},u =>
      W.choose(Result<W.Stop,List<&2,U32>>,Bool.not(U32.is_eq(W.count(U32,V.fields_of(V.constructors_of(types,p),o)),0)),u => Fail{W.Refused{"invoke","structured-argument"}},u =>
        H.bind(List<&2,U32>,List<&2,U32>,arguments(ps,os,types),words => Done{Con{H.immediate(o),words}}))))
    case _ _: Fail{W.Refused{"invoke","argument-arity"}}

def with_function(-B: Data, found: Maybe<&2,W.Function>, next: List<&2,U32> -> U32 -> Result<W.Stop,B>) -> Result<W.Stop,B>:
  match found:
    case None{}: Fail{W.Refused{"invoke","unknown-export"}}
    case Some{W.Function{name,parameters,result,slots,body}}: next(parameters,result)

# A Book request (SPEC §8) reads only the image: the export, its arguments and
# its describable result, before any fuel is spent.
def book(+plan: W.Plan, +booted: Booted, +name: List<&2,U32>, +fuel: U32, ordinals: List<&2,U32>) -> Result<W.Stop,Machine>:
  match plan booted:
    case W.Plan{entry,+types,+functions,reps} Booted{code,heap}:
      +index = E.function_index(functions,name,0)
      with_function(Machine,D.function_at(functions,index),parameters => +result =>
        H.bind(List<&2,U32>,Machine,arguments(parameters,ordinals,types),words =>
          W.choose(Result<W.Stop,Machine>,Bool.not(describable(U32.to_nat(W.none()),types,[result],Nil{})),u => Fail{W.Unsupported{"invoke","result-type"}},u =>
            Done{Machine{Enter{Callee{index},words},H.Stack{0,[H.Top{0}],3},heap,Meter{fuel,0,0},Nil{}}})))

def program(+plan: W.Plan, +booted: Booted, +fuel: U32) -> Machine:
  match plan booted:
    case W.Plan{entry,types,+functions,reps} Booted{code,heap}:
      Machine{Enter{Callee{E.function_index(functions,D.main_bytes(),0)},Nil{}},H.Stack{0,[H.Top{1}],3},heap,Meter{fuel,0,0},Nil{}}

def code_of(booted: Booted) -> H.Code:
  match booted:
    case Booted{code,heap}: code

def result_type(+plan: W.Plan, +name: List<&2,U32>) -> U32:
  match plan:
    case W.Plan{entry,types,functions,reps}: V.callee_result(D.function_at(functions,E.function_index(functions,name,0)))

# A Book's answer is described, then `act` and the answer are dropped (SPEC §6.3, §8). A description
# that stops (a display bound, an ill-typed word, a request) leaves `act` and the answer owned.
def concluded(+code: H.Code, +t: U32, m: Machine) -> Result<W.Stop,Machine>:
  match m:
    case Machine{Finished{Answered{+w}},+stack,+heap,+meter,+out}:
      Done{settled(H.bind(List<&2,U32>,Machine,described(code,heap,w,t),tree =>
        H.bind(H.Heap,Machine,H.drop(heap,H.room(stack),H.act_of(stack)),+heap2 =>
        H.bind(H.Heap,Machine,H.drop(heap2,H.room(stack),w),heap3 =>
          Done{Machine{Finished{Described{t,H.tag_of(code,heap,t,w),tree}},H.with_act(stack,0),heap3,meter,out}}))),
        Machine{Return{w},stack,heap,meter,out})}
    case _: Done{m}
