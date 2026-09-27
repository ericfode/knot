import Base

# Rung A. The accepted machine, tightened: one line per arm, columns aligned,
# each law directly under the mechanism it constrains, proof arms mirroring it.

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

def apply(frame: Frame, value: Payload) -> Payload:
  match frame value:
    case Unary{factor,bias} OwnedWord{x}: OwnedWord{U32.add(U32.mul(x,factor),bias)}
    case Binary{OwnedWord{a}} OwnedWord{b}: OwnedWord{U32.add(U32.mul(a,31),b)}

def step_parts(dest: U32, n: Nat, p: Payload, frames: List<&1,Frame>) -> Run:
  match n frames:
    case 1n+k _:             Checkpoint{Work{dest,k,tick_owned(p),frames}}
    case 0n   Nil{}:         Delivered{dest,p}
    case 0n   Con{frame,rest}: Checkpoint{Work{dest,0n,apply(frame,p),rest}}

def step(t: Task) -> Run:
  match t:
    case Work{dest,n,p,frames}: step_parts(dest,n,p,frames)

def run(fuel: Nat, state: Run) -> Run:
  match fuel state:
    case 0n   _:                state
    case 1n+n Checkpoint{task}: run(n,step(task))
    case 1n+n Delivered{d,p}:   Delivered{d,p}

law zero_fuel:
  for -r: Run
  {run(0n,r)
   == r
   : Run}
def zero_fuel(r): {==}

law delivered_absorbs:
  for n: Nat
  for d: U32
  for -p: Payload
  {run(n,Delivered{d,p})
   == Delivered{d,p}
   : Run}
def delivered_absorbs(n,d,p):
  match n:
    case 0n:   {==}
    case 1n+k: {==}

law fuel_add:
  for n: Nat
  for m: Nat
  for r: Run
  {run(m,run(n,r))
   == run(Nat.add(n,m),r)
   : Run}
def fuel_add(n,m,r):
  match n r:
    case 0n   _:                {==}
    case 1n+k Checkpoint{task}: fuel_add(k,m,step(task))
    case 1n+k Delivered{d,p}:   delivered_absorbs(m,d,p)

def slices(count: Nat, +quantum: Nat, state: Run) -> Run:
  match count:
    case 0n:   state
    case 1n+n: slices(n,quantum,run(quantum,state))
