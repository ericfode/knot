import Base

# Type, not Data: neither a task nor its saved payload may be copied.
type Payload is Type:
  OwnedWord{value: U32}

type Frame is Type:
  Unary{factor: U32, bias: U32}
  Binary{left: Payload}

type Task is Type:
  Work{destination: U32, remaining: Nat, payload: Payload, frames: List<&1,Frame>}

type Run is Type:
  Checkpoint{task: Task}
  Delivered{destination: U32, payload: Payload}

def tick(x: U32) -> U32:
  U32.add(U32.mul(x,1664525),1013904223)

def tick_owned(p: Payload) -> Payload:
  match p:
    case OwnedWord{x}: OwnedWord{tick(x)}

def combine(left: Payload, right: Payload) -> Payload:
  match left right:
    case OwnedWord{a} OwnedWord{b}: OwnedWord{U32.add(U32.mul(a,31),b)}

def unary(p: Payload, factor: U32, bias: U32) -> Payload:
  match p:
    case OwnedWord{x}: OwnedWord{U32.add(U32.mul(x,factor),bias)}

def apply(frame: Frame, value: Payload) -> Payload:
  match frame:
    case Unary{factor,bias}: unary(value,factor,bias)
    case Binary{left}: combine(left,value)

def step_parts(dest: U32, n: Nat, p: Payload, frames: List<&1,Frame>) -> Run:
  match n frames:
    case 1n+k _:
      Checkpoint{Work{dest,k,tick_owned(p),frames}}
    case 0n Nil{}:
      Delivered{dest,p}
    case 0n Con{frame,rest}:
      Checkpoint{Work{dest,0n,apply(frame,p),rest}}

def step(t: Task) -> Run:
  match t:
    case Work{dest,n,p,frames}: step_parts(dest,n,p,frames)

# Delivered is absorbing. Zero fuel preserves the whole residual state.
def run(fuel: Nat, state: Run) -> Run:
  match fuel state:
    case 0n _:
      state
    case 1n+n Checkpoint{task}:
      run(n,step(task))
    case 1n+n Delivered{dest,payload}:
      Delivered{dest,payload}

def slices(count: Nat, +quantum: Nat, state: Run) -> Run:
  match count:
    case 0n: state
    case 1n+n: slices(n,quantum,run(quantum,state))

def start(dest: U32, ticks: Nat, seed: U32, frames: List<&1,Frame>) -> Run:
  Checkpoint{Work{dest,ticks,OwnedWord{seed},frames}}

# Observations consume the owner. They cannot return a reusable task snapshot.
def observe_payload(p: Payload) -> U32:
  match p:
    case OwnedWord{x}: x

def observe(r: Run) -> U32 & U32 & U32:
  match r:
    case Checkpoint{Work{dest,n,p,frames}}: (0,dest,observe_payload(p))
    case Delivered{dest,p}: (1,dest,observe_payload(p))
