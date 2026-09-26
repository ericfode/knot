import Base
import ./task.bend as T
import ./LAWS.bend as L

def L.put_empty(A,x): {==}
def L.put_full(A,x,y): {==}
def L.take_full(A,x): {==}
def L.take_empty(A): {==}
def L.put_take(A,x): {==}
def L.take_twice(A,x): {==}
def L.zero_fuel(r): {==}
def L.delivered_absorbs(n,d,p):
  match n:
    case 0n: {==}
    case 1n+k: {==}
def L.one_tick(d,n,x,fs): {==}
def L.binary_order(d,a,b): {==}
def L.frame_captures(d,x,f,b): {==}
def L.fuel_add(n,m,r):
  match n r:
    case 0n _: {==}
    case 1n+k T.Checkpoint{task}:
      L.fuel_add(k,m,T.step(task))
    case 1n+k T.Delivered{d,p}:
      L.delivered_absorbs(m,d,p)
