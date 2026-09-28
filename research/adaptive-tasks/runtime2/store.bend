import Base
import ./protocol.bend as P

def data(value: P.Object) -> Bool:
  match value:
    case P.Object{id,1,rc,tag,children}: True{}
    case _: False{}

def data_edges(edges: List<&2,U32>, +objects: List<&2,P.Object>) -> Bool:
  match edges:
    case Nil{}: True{}
    case Con{h,t}: Bool.and(data(P.find(objects,h)),data_edges(t,objects))

def construct(+state: P.State, +dst: U32, +kind: U32, +tag: U32, +first: U32, +count: U32) -> P.State:
  match state:
    case P.State{P.Config{oc,+cap,pc,jc,+arity,rc,+ceiling,ac,ic},P.Store{+next,+readers,+freed,+objects,+captures,+pending},joins,status,reply}:
      +edges = P.slice(captures,first,count)
      +valid = Bool.and(U32.is_lt(dst,cap),Bool.and(U32.is_le(kind,1),Bool.and(P.range(first,count,cap),
        Bool.and(Bool.not(P.inside(dst,first,count)),Bool.and(U32.is_eq(P.at(U32,captures,dst,0),0),
        Bool.and(P.occupied(edges),Bool.or(U32.is_eq(kind,0),data_edges(edges,objects))))))))
      P.choose(P.State,valid,u =>
        P.choose(P.State,Bool.and(U32.is_le(count,arity),Bool.and(U32.is_ne(next,0),P.room(objects))),u =>
          P.stored(state,P.Store{P.choose(U32,U32.is_eq(next,ceiling),u => 0,u => U32.add(next,1)),readers,freed,
            P.insert(objects,P.Object{next,kind,1,tag,edges}),P.put(U32,P.clear(captures,first,count),dst,next),pending}),
          u => P.result(state,3,0)),u => P.result(state,1,0))

def retained(value: P.Object, +objects: List<&2,P.Object>, +limit: U32) -> Result<U32,List<&2,P.Object>>:
  match value:
    case P.Free{}: Fail{5}
    case P.Object{+id,1,+rc,+tag,+children}:
      P.choose(Result<U32,List<&2,P.Object>>,U32.is_lt(rc,limit),
        u => Done{P.replace(objects,id,P.Object{id,1,U32.add(rc,1),tag,children})},u => Fail{3})
    case _: Fail{2}

def share_result(result: Result<U32,List<&2,P.Object>>, +state: P.State, +dst: U32, +id: U32) -> P.State:
  match result state:
    case Fail{error} _: P.result(state,error,0)
    case Done{objects} P.State{config,P.Store{next,readers,freed,old,captures,pending},joins,status,reply}:
      P.stored(state,P.Store{next,readers,freed,objects,P.put(U32,captures,dst,id),pending})

def share(+state: P.State, +src: U32, +dst: U32) -> P.State:
  match state:
    case P.State{P.Config{oc,+cap,pc,jc,arity,+limit,ceiling,ac,ic},P.Store{next,readers,freed,+objects,+captures,pending},joins,status,reply}:
      +id = P.at(U32,captures,src,0)
      P.choose(P.State,Bool.and(U32.is_lt(src,cap),Bool.and(U32.is_lt(dst,cap),
        Bool.and(U32.is_ne(id,0),U32.is_eq(P.at(U32,captures,dst,0),0)))),u =>
          share_result(retained(P.find(objects,id),objects,limit),state,dst,id),u => P.result(state,1,0))

def move(+state: P.State, +src: U32, +dst: U32) -> P.State:
  match state:
    case P.State{P.Config{oc,+cap,pc,jc,arity,limit,ceiling,ac,ic},P.Store{+next,+readers,+freed,+objects,+captures,+pending},joins,status,reply}:
      +id = P.at(U32,captures,src,0)
      P.choose(P.State,Bool.and(U32.is_lt(src,cap),Bool.and(U32.is_lt(dst,cap),
        Bool.and(U32.is_ne(id,0),U32.is_eq(P.at(U32,captures,dst,0),0)))),u =>
          P.stored(state,P.Store{next,readers,freed,objects,P.put(U32,P.put(U32,captures,src,0),dst,id),pending}),
          u => P.result(state,1,0))

# Speculative retains include repeated child identities before any publication.
def acquire(edges: List<&2,U32>, +objects: List<&2,P.Object>, +limit: U32) -> Result<U32,List<&2,P.Object>>:
  match edges:
    case Nil{}: Done{objects}
    case Con{+h,+t}:
      P.bind(List<&2,P.Object>,List<&2,P.Object>,retained(P.find(objects,h),objects,limit),next => acquire(t,next,limit))

def open_shared(result: Result<U32,List<&2,P.Object>>, +state: P.State, value: P.Object, src: U32, first: U32) -> P.State:
  match result state value:
    case Fail{error} _ _: P.result(state,error,0)
    case Done{objects} P.State{config,P.Store{next,readers,freed,old,captures,pending},joins,status,reply} P.Object{+id,kind,rc,tag,+children}:
      P.stored(state,P.Store{next,readers,freed,P.replace(objects,id,P.Object{id,kind,U32.sub(rc,1),tag,children}),
        P.write(P.put(U32,captures,src,0),first,children),pending})
    case _ _ _: P.result(state,5,0)

def open_value(value: P.Object, +state: P.State, +src: U32, +first: U32, count: U32) -> P.State:
  match value state:
    case P.Free{} _: P.result(state,5,0)
    case P.Object{+id,+kind,+rc,+tag,+children} P.State{P.Config{oc,cap,pc,jc,arity,+limit,ceiling,ac,ic},P.Store{+next,+readers,+freed,+objects,+captures,+pending},joins,status,reply}:
      P.choose(P.State,U32.is_eq(P.length(U32,children),count),u =>
        P.choose(P.State,U32.is_eq(readers,0),u =>
          P.choose(P.State,Bool.and(U32.is_eq(kind,1),U32.is_gt(rc,1)),u =>
            open_shared(acquire(children,objects,limit),state,P.Object{id,kind,rc,tag,children},src,first),u =>
            P.stored(state,P.Store{next,readers,U32.add(freed,1),P.replace(objects,id,P.Free{}),
              P.write(P.put(U32,captures,src,0),first,children),pending})),u => P.result(state,3,0)),
        u => P.result(state,1,0))

def open(+state: P.State, +src: U32, +first: U32, +count: U32) -> P.State:
  match state:
    case P.State{P.Config{oc,+cap,pc,jc,arity,limit,ceiling,ac,ic},P.Store{next,readers,freed,+objects,+captures,pending},joins,status,reply}:
      +id = P.at(U32,captures,src,0)
      P.choose(P.State,Bool.and(U32.is_lt(src,cap),Bool.and(U32.is_ne(id,0),
        Bool.and(P.range(first,count,cap),Bool.and(Bool.not(P.inside(src,first,count)),P.vacant(P.slice(captures,first,count)))))),
        u => open_value(P.find(objects,id),state,src,first,count),u => P.result(state,1,0))

def release(+state: P.State, +src: U32) -> P.State:
  match state:
    case P.State{P.Config{oc,+cap,+pc,jc,arity,limit,ceiling,ac,ic},P.Store{+next,+readers,+freed,+objects,+captures,+pending},joins,status,reply}:
      +id = P.at(U32,captures,src,0)
      P.choose(P.State,Bool.and(U32.is_lt(src,cap),U32.is_ne(id,0)),u =>
        P.choose(P.State,U32.is_lt(P.length(U32,pending),pc),u =>
          P.stored(state,P.Store{next,readers,freed,objects,P.put(U32,captures,src,0),P.append(U32,pending,[id])}),
          u => P.result(state,3,0)),u => P.result(state,1,0))

type Pop is Data:
  Pop{rest: List<&2,U32>, last: U32}

def prefix(result: Pop, head: U32) -> Pop:
  match result:
    case Pop{rest,last}: Pop{Con{head,rest},last}

def pop(xs: List<&2,U32>) -> Pop:
  match xs:
    case Nil{}: Pop{Nil{},0}
    case Con{h,Nil{}}: Pop{Nil{},h}
    case Con{h,t}: prefix(pop(t),h)

def drop_value(value: P.Object, +state: P.State, +rest: List<&2,U32>) -> P.State:
  match value state:
    case P.Free{} _: P.result(state,5,0)
    case P.Object{+id,+kind,+rc,+tag,+children} P.State{P.Config{oc,cap,+pc,jc,arity,limit,ceiling,ac,ic},P.Store{+next,+readers,+freed,+objects,+captures,pending},joins,status,reply}:
      P.choose(P.State,Bool.and(U32.is_eq(kind,1),U32.is_gt(rc,1)),u =>
        P.stored(state,P.Store{next,readers,freed,P.replace(objects,id,P.Object{id,kind,U32.sub(rc,1),tag,children}),captures,rest}),u =>
        P.choose(P.State,P.range(P.length(U32,rest),P.length(U32,children),pc),u =>
          P.stored(state,P.Store{next,readers,U32.add(freed,1),P.replace(objects,id,P.Free{}),captures,P.append(U32,rest,children)}),
          u => P.result(state,3,0)))

def drop_last(result: Pop, +state: P.State) -> P.State:
  match result state:
    case Pop{rest,last} P.State{config,P.Store{next,readers,freed,objects,captures,pending},joins,status,reply}:
      drop_value(P.find(objects,last),state,rest)

def clean(budget: Nat, +state: P.State) -> P.State:
  match budget state:
    case _ P.State{config,P.Store{next,0,freed,objects,captures,Nil{}},joins,status,reply}: P.result(state,0,0)
    case 0n _: P.result(state,3,0)
    case 1n+n P.State{config,P.Store{next,+readers,freed,objects,captures,+pending},joins,status,reply}:
      P.choose(P.State,U32.is_eq(readers,0),u =>
        (+after = drop_last(pop(pending),state)
         P.choose(P.State,U32.is_eq(P.status(after),0),u => clean(n,after),u => after)),u => P.result(state,3,0))

def readers(state: P.State, count: U32) -> P.State:
  match state:
    case P.State{config,P.Store{next,old,freed,objects,captures,pending},joins,status,reply}:
      P.State{config,P.Store{next,count,freed,objects,captures,pending},joins,0,0}

def inspected(value: P.Object, state: P.State) -> P.State:
  match value:
    case P.Free{}: P.result(state,5,0)
    case P.Object{id,kind,rc,tag,children}: P.result(state,0,tag)

def inspect(+state: P.State, +src: U32) -> P.State:
  match state:
    case P.State{P.Config{oc,cap,pc,jc,arity,limit,ceiling,ac,ic},P.Store{next,readers,freed,+objects,+captures,pending},joins,status,reply}:
      +id = P.at(U32,captures,src,0)
      P.choose(P.State,Bool.and(U32.is_lt(src,cap),U32.is_ne(id,0)),u => inspected(P.find(objects,id),state),u => P.result(state,1,0))
