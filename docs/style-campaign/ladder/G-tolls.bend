import Base

# Rung G. The algebra of F with the vocabulary of B. Every frame is a toll on the
# purse: multiply by a rate, then add a fee. The clock charges interest. Paying
# one toll after another is one toll, so a whole task is a single bill waiting
# for the purse it will be charged to. `give` still pays one toll per tick;
# `bill` reads the same debt all at once, and `bill_agrees` is one witness.

# coins ↦ times·coins + plus. A toll may be copied; a purse may not.
type Toll is Data:
  Toll{times: U32, plus: U32}

def charge(toll: Toll, coins: U32) -> U32:
  match toll:
    case Toll{times,plus}: U32.add(U32.mul(times,coins),plus)

# Paying `first` and then `second` is one toll.
def compound(first: Toll, second: Toll) -> Toll:
  match first second:
    case Toll{t1,p1} Toll{+t2,p2}: Toll{U32.mul(t2,t1),U32.add(U32.mul(t2,p1),p2)}

def free() -> Toll: Toll{1,0}
def interest() -> Toll: Toll{1664525,1013904223}
def rate(times: U32, plus: U32) -> Toll: Toll{times,plus}
def levy(other: U32) -> Toll: Toll{1,U32.mul(other,31)}

type Purse is Type:
  Coins{value: U32}

def pay_toll(toll: Toll, purse: Purse) -> Purse:
  match purse:
    case Coins{coins}: Coins{charge(toll,coins)}

type Owed is Type:
  Owed{to: U32, ticks: Nat, purse: Purse, tolls: List<&2,Toll>}

type Held is Type:
  Still{owed: Owed}
  Kept{to: U32, purse: Purse}

def pay(to: U32, ticks: Nat, purse: Purse, tolls: List<&2,Toll>) -> Held:
  match ticks tolls:
    case 1n+k _:              Still{Owed{to,k,pay_toll(interest(),purse),tolls}}
    case 0n   Nil{}:          Kept{to,purse}
    case 0n   Con{toll,rest}: Still{Owed{to,0n,pay_toll(toll,purse),rest}}

def owe(o: Owed) -> Held:
  match o:
    case Owed{to,ticks,purse,tolls}: pay(to,ticks,purse,tolls)

def give(time: Nat, held: Held) -> Held:
  match time held:
    case 0n   _:              held
    case 1n+t Still{o}:       give(t,owe(o))
    case 1n+t Kept{to,purse}: Kept{to,purse}

def give_all(budgets: List<&2,Nat>, held: Held) -> Held:
  match budgets:
    case Nil{}:          held
    case Con{time,rest}: give_all(rest,give(time,held))

# The whole debt as one toll: interest for every tick, then every toll in order.
def bill(ticks: Nat, tolls: List<&2,Toll>) -> Toll:
  match ticks tolls:
    case 1n+k _:              compound(interest(),bill(k,tolls))
    case 0n   Nil{}:          free()
    case 0n   Con{toll,rest}: compound(toll,bill(0n,rest))

law no_time:
  for -h: Held
  {give(0n,h) == h : Held}
def no_time(h): {==}

law kept_stays:
  for t: Nat
  for to: U32
  for -purse: Purse
  {give(t,Kept{to,purse}) == Kept{to,purse} : Held}
def kept_stays(t,to,purse):
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
    case 0n   _:              {==}
    case 1n+k Still{o}:       time_adds(k,m,owe(o))
    case 1n+k Kept{to,purse}: kept_stays(m,to,purse)

law two_budgets:
  for n: Nat
  for m: Nat
  for h: Held
  {give_all([n,m],h) == give(Nat.add(n,m),h) : Held}
def two_budgets(n,m,h): time_adds(n,m,h)

# One witness: paying tick by tick and paying the bill agree on a two-toll debt.
law bill_agrees:
  {give(4n,Still{Owed{7,1n,Coins{5},[rate(3,1),levy(2)]}})
   == Kept{7,Coins{charge(bill(1n,[rate(3,1),levy(2)]),5)}}
   : Held}
def bill_agrees(): {==}
