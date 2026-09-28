import Base
import ./protocol.bend as P
import ./store.bend as S
import ./scheduler.bend as J
import ./observe.bend as O

def span(+state: P.State, +base: U32, +count: U32, +stride: U32, +limit: U32) -> P.State:
  P.choose(P.State,U32.is_eq(stride,0),u => P.result(state,1,0),u =>
    P.choose(P.State,U32.is_le(base,limit),u =>
      P.choose(P.State,U32.is_le(count,U32.div(U32.sub(limit,base),stride)),
        u => P.result(state,0,U32.add(base,U32.mul(count,stride))),u => P.result(state,3,0)),
      u => P.result(state,3,0)))

def operands(command: P.Command) -> Bool:
  match command:
    case P.Command{1,a,b,c,d,e,f,g}: P.vacant([f,g])
    case P.Command{2,a,b,c,d,e,f,g}: P.vacant([c,d,e,f,g])
    case P.Command{3,a,b,c,d,e,f,g}: P.vacant([c,d,e,f,g])
    case P.Command{4,a,b,c,d,e,f,g}: P.vacant([d,e,f,g])
    case P.Command{5,a,b,c,d,e,f,g}: P.vacant([b,c,d,e,f,g])
    case P.Command{6,a,b,c,d,e,f,g}: P.vacant([b,c,d,e,f,g])
    case P.Command{7,a,b,c,d,e,f,g}: P.vacant([b,c,d,e,f,g])
    case P.Command{8,a,b,c,d,e,f,g}: P.vacant([f,g])
    case P.Command{9,a,b,c,d,e,f,g}: P.vacant([e,f,g])
    case P.Command{10,a,b,c,d,e,f,g}: P.vacant([c,d,e,f,g])
    case P.Command{11,a,b,c,d,e,f,g}: P.vacant([d,e,f,g])
    case P.Command{12,a,b,c,d,e,f,g}: P.vacant([b,c,d,e,f,g])
    case P.Command{13,a,b,c,d,e,f,g}: P.vacant([e,f,g])
    case _: False{}

def execute(command: P.Command, state: P.State) -> P.State:
  match command:
    case P.Command{1,a,b,c,d,e,f,g}: S.construct(state,a,b,c,d,e)
    case P.Command{2,a,b,c,d,e,f,g}: S.share(state,a,b)
    case P.Command{3,a,b,c,d,e,f,g}: S.move(state,a,b)
    case P.Command{4,a,b,c,d,e,f,g}: S.open(state,a,b,c)
    case P.Command{5,a,b,c,d,e,f,g}: S.release(state,a)
    case P.Command{6,a,b,c,d,e,f,g}: S.clean(U32.to_nat(a),state)
    case P.Command{7,a,b,c,d,e,f,g}: S.readers(state,a)
    case P.Command{8,a,b,c,d,e,f,g}: J.start(state,a,b,c,d,e)
    case P.Command{9,a,b,c,d,e,f,g}: J.deliver(state,a,b,c,d)
    case P.Command{10,a,b,c,d,e,f,g}: J.cancel(state,a,b)
    case P.Command{11,a,b,c,d,e,f,g}: J.resume(state,a,b,c)
    case P.Command{12,a,b,c,d,e,f,g}: S.inspect(state,a)
    case P.Command{13,a,b,c,d,e,f,g}: span(state,a,b,c,d)
    case _: P.result(state,2,0)

def step(+command: P.Command, +state: P.State) -> P.State:
  match command:
    case P.Command{+op,a,b,c,d,e,f,g}:
      P.choose(P.State,Bool.and(U32.is_ge(op,1),U32.is_le(op,13)),u =>
        P.choose(P.State,operands(command),u => execute(command,state),u => P.result(state,1,0)),
        u => P.result(state,2,0))

def initial(config: P.Config) -> P.State:
  P.initial(config)

def observe(state: P.State) -> String:
  O.state(state)

def run(commands: List<&2,P.Command>, state: P.State) -> P.State:
  match commands:
    case Nil{}: state
    case Con{head,tail}: run(tail,step(head,state))
