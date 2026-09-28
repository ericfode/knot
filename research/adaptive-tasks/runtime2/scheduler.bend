import Base
import ./protocol.bend as P

def overlap(+first: U32, +count: U32, +other: U32, +size: U32) -> Bool:
  Bool.and(U32.is_ne(count,0),Bool.and(U32.is_ne(size,0),Bool.or(P.inside(first,other,size),P.inside(other,first,count))))

def reserved(joins: List<&2,P.Join>, +first: U32, +count: U32) -> Bool:
  match joins:
    case Nil{}: False{}
    case Con{P.Join{attempt,+phase,arity,received,completions,code,base,size,results},tail}:
      Bool.or(Bool.and(Bool.or(U32.is_eq(phase,1),U32.is_eq(phase,2)),overlap(first,count,base,size)),reserved(tail,first,count))

def start_join(join: P.Join, +state: P.State, +index: U32, +arity: U32, +code: U32, +base: U32, +count: U32) -> P.State:
  match join state:
    case P.Join{+attempt,+phase,oldarity,received,+completions,oldcode,oldbase,oldcount,results}
      P.State{P.Config{oc,cc,pc,jc,+limit,rc,ceiling,+attemptLimit,ic},P.Store{next,readers,freed,objects,captures,pending},+joins,status,reply}:
          P.choose(P.State,Bool.and(Bool.or(U32.is_eq(phase,0),Bool.or(U32.is_eq(phase,3),U32.is_eq(phase,4))),
            Bool.not(reserved(joins,base,count))),u =>
            P.choose(P.State,Bool.and(U32.is_le(arity,limit),U32.is_lt(attempt,attemptLimit)),u =>
              P.updated(state,P.Store{next,readers,freed,objects,captures,pending},
                P.put(P.Join,joins,index,P.Join{U32.add(attempt,1),Bool.pick(U32,U32.is_eq(arity,0),2,1),arity,0,
                  U32.add(completions,Bool.pick(U32,U32.is_eq(arity,0),1,0)),code,base,count,P.repeat(U32,U32.to_nat(arity),0)}),0,0),
              u => P.result(state,3,0)),u => P.result(state,1,0))

def start(+state: P.State, +index: U32, +arity: U32, +code: U32, +base: U32, +count: U32) -> P.State:
  match state:
    case P.State{P.Config{oc,cap,pc,jc,limit,rc,ceiling,ac,ic},store,+joins,status,reply}:
      P.choose(P.State,Bool.and(U32.is_lt(index,jc),Bool.and(U32.is_lt(code,ic),P.range(base,count,cap))),
        u => start_join(P.at(P.Join,joins,index,P.empty_join()),state,index,arity,code,base,count),u => P.result(state,1,0))

def deliver_join(join: P.Join, +state: P.State, +index: U32, attempt: U32, +slot: U32, +src: U32, +id: U32) -> P.State:
  match join state:
    case P.Join{+current,phase,+arity,+received,+completions,+code,+base,+count,+results}
      P.State{config,P.Store{+next,+readers,+freed,+objects,+captures,+pending},+joins,status,reply}:
      P.choose(P.State,Bool.and(U32.is_eq(current,attempt),Bool.and(U32.is_eq(phase,1),
        Bool.and(U32.is_lt(slot,arity),U32.is_eq(P.at(U32,results,slot,0),0)))),u =>
        P.updated(state,P.Store{next,readers,freed,objects,P.put(U32,captures,src,0),pending},
          P.put(P.Join,joins,index,P.Join{current,Bool.pick(U32,U32.is_eq(U32.add(received,1),arity),2,1),arity,U32.add(received,1),
            U32.add(completions,Bool.pick(U32,U32.is_eq(U32.add(received,1),arity),1,0)),code,base,count,P.put(U32,results,slot,id)}),0,0),
        u => P.result(state,1,0))

def deliver(+state: P.State, +index: U32, +attempt: U32, +slot: U32, +src: U32) -> P.State:
  match state:
    case P.State{P.Config{oc,cap,pc,jc,arity,limit,ceiling,ac,ic},P.Store{next,readers,freed,objects,+captures,pending},+joins,status,reply}:
      +id = P.at(U32,captures,src,0)
      P.choose(P.State,Bool.and(U32.is_lt(index,jc),Bool.and(U32.is_lt(src,cap),U32.is_ne(id,0))),
        u => deliver_join(P.at(P.Join,joins,index,P.empty_join()),state,index,attempt,slot,src,id),u => P.result(state,1,0))

def cancel_join(join: P.Join, +state: P.State, +index: U32, attempt: U32) -> P.State:
  match join state:
    case P.Join{+current,+phase,+arity,received,+completions,+code,+base,+count,+results}
      P.State{P.Config{oc,cap,+pc,jc,limit,rc,ceiling,ac,ic},P.Store{+next,+readers,+freed,+objects,+captures,+pending},+joins,status,reply}:
          P.choose(P.State,Bool.and(U32.is_eq(current,attempt),Bool.or(U32.is_eq(phase,1),U32.is_eq(phase,2))),u =>
            (+owned = P.append(U32,P.live(P.slice(captures,base,count)),P.live(results))
             P.choose(P.State,P.range(P.length(U32,pending),P.length(U32,owned),pc),u =>
               P.updated(state,P.Store{next,readers,freed,objects,P.clear(captures,base,count),P.append(U32,pending,owned)},
                 P.put(P.Join,joins,index,P.Join{current,3,arity,0,completions,code,base,count,P.repeat(U32,U32.to_nat(arity),0)}),0,0),
               u => P.result(state,3,0))),u => P.result(state,1,0))

def cancel(+state: P.State, +index: U32, +attempt: U32) -> P.State:
  match state:
    case P.State{P.Config{oc,cap,pc,jc,arity,limit,ceiling,ac,ic},store,+joins,status,reply}:
      P.choose(P.State,U32.is_lt(index,jc),u => cancel_join(P.at(P.Join,joins,index,P.empty_join()),state,index,attempt),u => P.result(state,1,0))

def resume_join(join: P.Join, +state: P.State, +index: U32, attempt: U32, +first: U32) -> P.State:
  match join state:
    case P.Join{+current,phase,+arity,+received,+completions,+code,+base,+count,+results}
      P.State{P.Config{oc,cap,pc,jc,limit,rc,ceiling,ac,ic},P.Store{+next,+readers,+freed,+objects,+captures,+pending},+joins,status,reply}:
          P.choose(P.State,Bool.and(U32.is_eq(current,attempt),Bool.and(U32.is_eq(phase,2),
            Bool.and(P.range(first,arity,cap),P.vacant(P.slice(captures,first,arity))))),u =>
              P.updated(state,P.Store{next,readers,freed,objects,P.write(captures,first,results),pending},
                P.put(P.Join,joins,index,P.Join{current,4,arity,received,completions,code,base,count,P.repeat(U32,U32.to_nat(arity),0)}),0,code),
              u => P.result(state,1,0))

def resume(+state: P.State, +index: U32, +attempt: U32, +first: U32) -> P.State:
  match state:
    case P.State{P.Config{oc,cap,pc,jc,arity,limit,ceiling,ac,ic},store,+joins,status,reply}:
      P.choose(P.State,U32.is_lt(index,jc),u => resume_join(P.at(P.Join,joins,index,P.empty_join()),state,index,attempt,first),u => P.result(state,1,0))
