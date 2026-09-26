import Base

# Independent sequence model. No implementation imports or array operations.
type Op is Data:
  Push{x: U32}
  Pop{}
  Get{i: U32}
  Set{i: U32, x: U32}
  Swap{i: U32, x: U32}
  Reserve{minimum: U32}
  Slice{start: U32, end: U32}

type Observation is Data:
  Ok{}
  Value{x: U32}
  Values{xs: List<&2,U32>}
  BadIndex{}
  IsEmpty{}
  AtLimit{}
  BadRange{}

type State is Data:
  Sequence{items: List<&2,U32>, max: U32}

def length(xs: List<&2,U32>) -> U32:
  U32.from_nat(List.length(&2,U32,xs))

def append(xs: List<&2,U32>, value: U32) -> List<&2,U32>:
  match xs:
    case Nil{}:
      Con{value,Nil{}}
    case Con{x,tail}:
      Con{x,append(tail,value)}

def get(xs: List<&2,U32>, i: Nat) -> Observation:
  match xs:
    case Nil{}:
      BadIndex{}
    case Con{x,tail}:
      match i:
        case 0n:
          Value{x}
        case 1n+p:
          get(tail,p)

def set(xs: List<&2,U32>, i: Nat, value: U32) -> List<&2,U32>:
  match xs:
    case Nil{}:
      Nil{}
    case Con{x,tail}:
      match i:
        case 0n:
          Con{value,tail}
        case 1n+p:
          Con{x,set(tail,p,value)}

def pop_tail(x: U32, pair: List<&2,U32> & Observation) -> List<&2,U32> & Observation:
  (xs,result) = pair
  (Con{x,xs},result)

def pop(xs: List<&2,U32>) -> List<&2,U32> & Observation:
  match xs:
    case Nil{}:
      (Nil{},IsEmpty{})
    case Con{x,tail}:
      match tail:
        case Nil{}:
          (Nil{},Value{x})
        case Con{y,rest}:
          pop_tail(x,pop(Con{y,rest}))

def popped(max: U32, pair: List<&2,U32> & Observation) -> State & Observation:
  (xs,result) = pair
  (Sequence{xs,max},result)

def push_if(+xs: List<&2,U32>, +max: U32, x: U32, valid: Bool) -> State & Observation:
  match valid:
    case False{}:
      (Sequence{xs,max},AtLimit{})
    case True{}:
      (Sequence{append(xs,x),max},Ok{})

def set_if(+xs: List<&2,U32>, max: U32, i: U32, x: U32, valid: Bool) -> State & Observation:
  match valid:
    case False{}:
      (Sequence{xs,max},BadIndex{})
    case True{}:
      (Sequence{set(xs,U32.to_nat(i),x),max},Ok{})

def swap_if(+xs: List<&2,U32>, max: U32, +i: U32, x: U32, valid: Bool) -> State & Observation:
  match valid:
    case False{}:
      (Sequence{xs,max},BadIndex{})
    case True{}:
      (Sequence{set(xs,U32.to_nat(i),x),max},get(xs,U32.to_nat(i)))

def reserve_if(xs: List<&2,U32>, max: U32, valid: Bool) -> State & Observation:
  match valid:
    case False{}:
      (Sequence{xs,max},AtLimit{})
    case True{}:
      (Sequence{xs,max},Ok{})

def slice_if(+xs: List<&2,U32>, max: U32, +start: U32, end: U32, valid: Bool) -> State & Observation:
  match valid:
    case False{}:
      (Sequence{xs,max},BadRange{})
    case True{}:
      (Sequence{xs,max},Values{List.take(&2,U32,List.drop(&2,U32,xs,U32.to_nat(start)),U32.to_nat(U32.sub(end,start)))})

def step(state: State, op: Op) -> State & Observation:
  match state:
    case Sequence{+xs,+max}:
      match op:
        case Push{x}:
          push_if(xs,max,x,U32.is_lt(length(xs),max))
        case Pop{}:
          popped(max,pop(xs))
        case Get{i}:
          (Sequence{xs,max},get(xs,U32.to_nat(i)))
        case Set{+i,x}:
          set_if(xs,max,i,x,U32.is_lt(i,length(xs)))
        case Swap{+i,x}:
          swap_if(xs,max,i,x,U32.is_lt(i,length(xs)))
        case Reserve{minimum}:
          reserve_if(xs,max,U32.is_le(minimum,max))
        case Slice{+start,+end}:
          slice_if(xs,max,start,end,Bool.and(U32.is_le(start,end),U32.is_le(end,length(xs))))

def list_eq(xs: List<&2,U32>, ys: List<&2,U32>) -> Bool:
  match xs:
    case Nil{}:
      match ys:
        case Nil{}:
          True{}
        case Con{h,t}:
          False{}
    case Con{x,xt}:
      match ys:
        case Nil{}:
          False{}
        case Con{y,yt}:
          Bool.and(U32.is_eq(x,y),list_eq(xt,yt))

def obs_eq(x: Observation, y: Observation) -> Bool:
  match x:
    case Ok{}:
      match y:
        case Ok{}: True{}
        case _: False{}
    case Value{a}:
      match y:
        case Value{b}: U32.is_eq(a,b)
        case _: False{}
    case Values{a}:
      match y:
        case Values{b}: list_eq(a,b)
        case _: False{}
    case BadIndex{}:
      match y:
        case BadIndex{}: True{}
        case _: False{}
    case IsEmpty{}:
      match y:
        case IsEmpty{}: True{}
        case _: False{}
    case AtLimit{}:
      match y:
        case AtLimit{}: True{}
        case _: False{}
    case BadRange{}:
      match y:
        case BadRange{}: True{}
        case _: False{}
