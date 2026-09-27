import Base
type W is Type:
  O{v: U32}
type F is Type:
  U{f: U32, b: U32}
  B{l: W}
type Q is Type:
  Q{d: U32, n: Nat, w: W, fs: List<&1,F>}
type H is Type:
  S{q: Q}
  K{d: U32, w: W}
def tk(x: U32) -> U32: U32.add(U32.mul(x,1664525),1013904223)
def ag(w: W) -> W:
  match w:
    case O{x}: O{tk(x)}
def st(f: F, w: W) -> W:
  match f w:
    case U{a,b} O{x}: O{U32.add(U32.mul(x,a),b)}
    case B{O{a}} O{b}: O{U32.add(U32.mul(a,31),b)}
def p(d: U32, n: Nat, w: W, fs: List<&1,F>) -> H:
  match n fs:
    case 1n+k _: S{Q{d,k,ag(w),fs}}
    case 0n Nil{}: K{d,w}
    case 0n Con{f,r}: S{Q{d,0n,st(f,w),r}}
def q(x: Q) -> H:
  match x:
    case Q{d,n,w,fs}: p(d,n,w,fs)
def g(t: Nat, h: H) -> H:
  match t h:
    case 0n _: h
    case 1n+t S{x}: g(t,q(x))
    case 1n+t K{d,w}: K{d,w}
def gs(ts: List<&2,Nat>, h: H) -> H:
  match ts:
    case Nil{}: h
    case Con{t,ts}: gs(ts,g(t,h))
law l0: for -h: H {g(0n,h) == h : H}
def l0(h): {==}
law l1: for t: Nat for d: U32 for -w: W {g(t,K{d,w}) == K{d,w} : H}
def l1(t,d,w):
  match t:
    case 0n: {==}
    case 1n+k: {==}
law l2: for n: Nat for m: Nat for h: H {g(m,g(n,h)) == g(Nat.add(n,m),h) : H}
def l2(n,m,h):
  match n h:
    case 0n _: {==}
    case 1n+k S{x}: l2(k,m,q(x))
    case 1n+k K{d,w}: l1(m,d,w)
law l3: for n: Nat for m: Nat for h: H {gs([n,m],h) == g(Nat.add(n,m),h) : H}
def l3(n,m,h): l2(n,m,h)
