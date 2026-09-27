import Base

# Rung F. Every frame is an affine map on the word, and so is the clock tick.
# A task is therefore a composition of affine maps waiting for its seed. The
# machine below still steps one frame at a time; `plan` is the same task read
# all at once, and `plan_agrees` is one concrete witness that they coincide.

# x ↦ k·x + c. Maps are Data and may be copied; the word they act on may not.
type Aff is Data:
  Aff{k: U32, c: U32}

def act(f: Aff, x: U32) -> U32:
  match f:
    case Aff{k,c}: U32.add(U32.mul(k,x),c)

# g after f: (k2·(k1·x + c1) + c2) = (k2·k1)·x + (k2·c1 + c2)
def then(f: Aff, g: Aff) -> Aff:
  match f g:
    case Aff{k1,c1} Aff{+k2,c2}: Aff{U32.mul(k2,k1),U32.add(U32.mul(k2,c1),c2)}

def same() -> Aff: Aff{1,0}
def clock() -> Aff: Aff{1664525,1013904223}
def scale(f: U32, b: U32) -> Aff: Aff{f,b}
def after(left: U32) -> Aff: Aff{1,U32.mul(left,31)}

type Purse is Type:
  Owned{value: U32}

def apply(f: Aff, w: Purse) -> Purse:
  match w:
    case Owned{x}: Owned{act(f,x)}

type Owed is Type:
  Owed{to: U32, ticks: Nat, purse: Purse, frames: List<&2,Aff>}

type Held is Type:
  Still{owed: Owed}
  Kept{to: U32, purse: Purse}

def pay(to: U32, ticks: Nat, w: Purse, frames: List<&2,Aff>) -> Held:
  match ticks frames:
    case 1n+k _:               Still{Owed{to,k,apply(clock(),w),frames}}
    case 0n   Nil{}:           Kept{to,w}
    case 0n   Con{frame,rest}: Still{Owed{to,0n,apply(frame,w),rest}}

def owe(o: Owed) -> Held:
  match o:
    case Owed{to,ticks,w,frames}: pay(to,ticks,w,frames)

def give(time: Nat, held: Held) -> Held:
  match time held:
    case 0n   _:          held
    case 1n+t Still{o}:   give(t,owe(o))
    case 1n+t Kept{to,w}: Kept{to,w}

# The whole task as one map: every tick composes the clock, then every frame.
def plan(ticks: Nat, frames: List<&2,Aff>) -> Aff:
  match ticks frames:
    case 1n+k _:               then(clock(),plan(k,frames))
    case 0n   Nil{}:           same()
    case 0n   Con{frame,rest}: then(frame,plan(0n,rest))

law no_time:
  for -h: Held
  {give(0n,h) == h : Held}
def no_time(h): {==}

law kept_stays:
  for t: Nat
  for to: U32
  for -w: Purse
  {give(t,Kept{to,w}) == Kept{to,w} : Held}
def kept_stays(t,to,w):
  match t:
    case 0n:   {==}
    case 1n+k: {==}

law time_adds:
  for n: Nat
  for m: Nat
  for h: Held
  {give(m,give(n,h)) == give(Nat.add(n,m),h) : Held}
def time_adds(n,m,h):
  match n h:
    case 0n   _:          {==}
    case 1n+k Still{o}:   time_adds(k,m,owe(o))
    case 1n+k Kept{to,w}: kept_stays(m,to,w)

# One concrete witness: stepping and planning agree on a two-frame task.
law plan_agrees:
  {give(4n,Still{Owed{7,1n,Owned{5},[scale(3,1),after(2)]}})
   == Kept{7,Owned{act(plan(1n,[scale(3,1),after(2)]),5)}}
   : Held}
def plan_agrees(): {==}
