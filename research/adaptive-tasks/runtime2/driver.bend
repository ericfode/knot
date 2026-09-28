import Base
import ./protocol.bend as P
import ./model.bend as M

type Frame is Data:
  Frame{pc: U32, phase: U32, state: P.State}

def initial(config: P.Config) -> Frame:
  Frame{0,0,M.initial(config)}

def limit(state: P.State) -> U32:
  match state:
    case P.State{P.Config{objects,captures,pending,joins,arity,rcLimit,idLimit,attemptLimit,count},store,results,status,reply}: count

def reply(state: P.State) -> U32:
  match state:
    case P.State{config,store,joins,status,value}: value

def fault(pc: U32, state: P.State, status: U32) -> Frame:
  Frame{pc,3,P.result(state,status,0)}

def advance(+pc: U32, +op: U32, +state: P.State) -> Frame:
  P.choose(Frame,U32.is_eq(P.status(state),0),u =>
    Frame{P.choose(U32,U32.is_eq(op,11),v => reply(state),v => U32.add(pc,1)),0,state},
    u => Frame{pc,P.choose(U32,U32.is_eq(P.status(state),3),v => 1,v => 3),state})

def branch(+pc: U32, +tag: U32, +yes: U32, +no: U32, +state: P.State) -> Frame:
  P.choose(Frame,U32.is_eq(P.status(state),0),u =>
    Frame{P.choose(U32,U32.is_eq(reply(state),tag),v => yes,v => no),0,P.result(state,0,0)},u => Frame{pc,3,state})

def halt(pc: U32, +state: P.State) -> Frame:
  Frame{pc,P.choose(U32,U32.is_eq(P.status(state),0),u => 2,u => 3),state}

def execute(command: P.Command, +pc: U32, +state: P.State) -> Frame:
  match command:
    case P.Command{14,+src,+tag,+yes,+no,e,f,g}:
      P.choose(Frame,Bool.and(U32.is_eq(U32.or(e,U32.or(f,g)),0),
        Bool.and(U32.is_lt(yes,limit(state)),U32.is_lt(no,limit(state)))),u =>
          branch(pc,tag,yes,no,M.step(P.Command{12,src,0,0,0,0,0,0},state)),u => fault(pc,state,1))
    case P.Command{15,+target,b,c,d,e,f,g}:
      P.choose(Frame,Bool.and(U32.is_eq(U32.or(b,U32.or(c,U32.or(d,U32.or(e,U32.or(f,g))))),0),
        U32.is_lt(target,limit(state))),u => Frame{target,0,P.result(state,0,0)},u => fault(pc,state,1))
    case P.Command{16,+src,b,c,d,e,f,g}:
      P.choose(Frame,U32.is_eq(U32.or(b,U32.or(c,U32.or(d,U32.or(e,U32.or(f,g))))),0),u =>
        halt(pc,M.step(P.Command{12,src,0,0,0,0,0,0},state)),u => fault(pc,state,1))
    case P.Command{17,a,b,c,d,e,f,g}:
      P.choose(Frame,U32.is_eq(U32.or(a,U32.or(b,U32.or(c,U32.or(d,U32.or(e,U32.or(f,g)))))),0),u =>
        Frame{U32.add(pc,1),1,P.result(state,0,0)},u => fault(pc,state,1))
    case P.Command{+op,a,b,c,d,e,f,g}:
      advance(pc,op,M.step(P.Command{op,a,b,c,d,e,f,g},state))

def fetch(+code: List<&2,P.Command>, +pc: U32, +state: P.State) -> Frame:
  P.choose(Frame,U32.is_lt(pc,P.length(P.Command,code)),u =>
    execute(P.at(P.Command,code,pc,P.Command{0,0,0,0,0,0,0,0}),pc,state),u => fault(pc,state,5))

# Phase zero continues; suspension is published before the next fuel check.
def continue(frame: Frame, next: Frame -> Frame) -> Frame:
  match frame:
    case Frame{pc,0,state}: next(Frame{pc,1,state})
    case Frame{pc,phase,state}: Frame{pc,phase,state}

def run(fuel: Nat, +code: List<&2,P.Command>, +frame: Frame) -> Frame:
  match fuel frame:
    case 0n _: frame
    case 1n+fuel Frame{pc,2,state}: frame
    case 1n+fuel Frame{pc,3,state}: frame
    case 1n+fuel Frame{pc,phase,state}:
      continue(fetch(code,pc,state),next => run(fuel,code,next))

def observe(frame: Frame) -> String:
  match frame:
    case Frame{pc,phase,state}:
      String.concat(["{\"pc\":",U32.show(pc),",\"phase\":",U32.show(phase),",\"state\":",M.observe(state),"}"])
