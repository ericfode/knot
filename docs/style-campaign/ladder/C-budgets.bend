import Base

# Rung C. The metaphor plus one more idea: time arrives as a list of budgets,
# and regrouping budgets is a law of the machine, not a scheduler's promise.

type Purse is Type:
  Owned{value: U32}

type Frame is Type:
  Unary{factor: U32, bias: U32}
  Binary{left: Purse}

type Owed is Type:
  Owed{to: U32, ticks: Nat, purse: Purse, frames: List<&1,Frame>}

type Held is Type:
  Still{owed: Owed}
  Kept{to: U32, purse: Purse}

def tick(x: U32) -> U32:
  U32.add(U32.mul(x,1664525),1013904223)

def age(w: Purse) -> Purse:
  match w:
    case Owned{x}: Owned{tick(x)}

def settle(frame: Frame, w: Purse) -> Purse:
  match frame w:
    case Unary{factor,bias} Owned{x}: Owned{U32.add(U32.mul(x,factor),bias)}
    case Binary{Owned{a}}   Owned{b}: Owned{U32.add(U32.mul(a,31),b)}

def pay(to: U32, ticks: Nat, w: Purse, frames: List<&1,Frame>) -> Held:
  match ticks frames:
    case 1n+k _:               Still{Owed{to,k,age(w),frames}}
    case 0n   Nil{}:           Kept{to,w}
    case 0n   Con{frame,rest}: Still{Owed{to,0n,settle(frame,w),rest}}

def owe(o: Owed) -> Held:
  match o:
    case Owed{to,ticks,w,frames}: pay(to,ticks,w,frames)

def give(time: Nat, held: Held) -> Held:
  match time held:
    case 0n   _:          held
    case 1n+t Still{o}:   give(t,owe(o))
    case 1n+t Kept{to,w}: Kept{to,w}

# A budget list is just time that arrives in pieces.
def give_all(budgets: List<&2,Nat>, held: Held) -> Held:
  match budgets:
    case Nil{}:          held
    case Con{time,rest}: give_all(rest,give(time,held))

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

law no_budgets:
  for -h: Held
  {give_all(Nil{},h) == h : Held}
def no_budgets(h): {==}

law two_budgets:
  for n: Nat
  for m: Nat
  for h: Held
  {give_all([n,m],h) == give(Nat.add(n,m),h) : Held}
def two_budgets(n,m,h): time_adds(n,m,h)
