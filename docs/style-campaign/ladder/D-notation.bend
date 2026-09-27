import Base
# Rung D. Notation. Read the rulers, then the columns.
# ── words ────────────────────────────────────────────────
type W is Type:
  O{v: U32}
type F is Type:
  U{f: U32, b: U32}
  B{l: W}
# ── what is owed, what is held ───────────────────────────
type Owed is Type:
  Owed{to: U32, n: Nat, w: W, fs: List<&1,F>}
type H is Type:
  S{o: Owed}
  K{to: U32, w: W}
# ── one tick, one frame ──────────────────────────────────
def tk(x: U32) -> U32: U32.add(U32.mul(x,1664525),1013904223)
def age(w: W) -> W:
  match w:
    case O{x}: O{tk(x)}
def st(f: F, w: W) -> W:
  match f w:
    case U{a,b} O{x}: O{U32.add(U32.mul(x,a),b)}
    case B{O{a}} O{b}: O{U32.add(U32.mul(a,31),b)}
# ── pay: ticks first, then frames, then keep ─────────────
def pay(to: U32, n: Nat, w: W, fs: List<&1,F>) -> H:
  match n fs:
    case 1n+k _:          S{Owed{to,k,age(w),fs}}
    case 0n   Nil{}:      K{to,w}
    case 0n   Con{f,rest}: S{Owed{to,0n,st(f,w),rest}}
def owe(o: Owed) -> H:
  match o:
    case Owed{to,n,w,fs}: pay(to,n,w,fs)
# ── give: 0 · h = h ; t+1 · S o = t · owe o ; t · K = K ──
def give(t: Nat, h: H) -> H:
  match t h:
    case 0n   _:       h
    case 1n+t S{o}:    give(t,owe(o))
    case 1n+t K{to,w}: K{to,w}
def gives(ts: List<&2,Nat>, h: H) -> H:
  match ts:
    case Nil{}:      h
    case Con{t,ts}:  gives(ts,give(t,h))
# ── laws, each under its rule ────────────────────────────
law zero: for -h: H {give(0n,h) == h : H}
def zero(h): {==}
law kept: for t: Nat for to: U32 for -w: W {give(t,K{to,w}) == K{to,w} : H}
def kept(t,to,w):
  match t:
    case 0n:   {==}
    case 1n+k: {==}
law adds: for n: Nat for m: Nat for h: H {give(m,give(n,h)) == give(Nat.add(n,m),h) : H}
def adds(n,m,h):
  match n h:
    case 0n   _:       {==}
    case 1n+k S{o}:    adds(k,m,owe(o))
    case 1n+k K{to,w}: kept(m,to,w)
law two: for n: Nat for m: Nat for h: H {gives([n,m],h) == give(Nat.add(n,m),h) : H}
def two(n,m,h): adds(n,m,h)
