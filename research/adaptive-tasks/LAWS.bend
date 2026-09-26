import Base
import ./slot.bend as S
import ./task.bend as T

law put_empty:
  for -A: Type
  for -x: A
  {S.put(A,S.Vacant{},x) == S.Inserted{S.Occupied{x}} : S.Put<A>}
law put_full:
  for -A: Type
  for -x: A
  for -y: A
  {S.put(A,S.Occupied{x},y) == S.Rejected{S.Occupied{x},y} : S.Put<A>}
law take_full:
  for -A: Type
  for -x: A
  {S.take(A,S.Occupied{x}) == S.Extracted{S.Vacant{},x} : S.Take<A>}
law take_empty:
  for -A: Type
  {S.take(A,S.Vacant{}) == S.Missing{S.Vacant{}} : S.Take<A>}
law put_take:
  for -A: Type
  for -x: A
  {S.take(A,S.put_slot(A,S.put(A,S.Vacant{},x))) == S.Extracted{S.Vacant{},x} : S.Take<A>}
law take_twice:
  for -A: Type
  for -x: A
  {S.take(A,S.take_slot(A,S.take(A,S.Occupied{x}))) == S.Missing{S.Vacant{}} : S.Take<A>}
law zero_fuel:
  for -r: T.Run
  {T.run(0n,r) == r : T.Run}
law delivered_absorbs:
  for n: Nat
  for d: U32
  for -p: T.Payload
  {T.run(n,T.Delivered{d,p}) == T.Delivered{d,p} : T.Run}
law one_tick:
  for d: U32
  for n: Nat
  for x: U32
  for -fs: List<&1,T.Frame>
  {T.run(1n,T.start(d,1n+n,x,fs)) == T.Checkpoint{T.Work{d,n,T.OwnedWord{U32.add(U32.mul(x,1664525),1013904223)},fs}} : T.Run}
law binary_order:
  for d: U32
  for a: U32
  for b: U32
  {T.run(2n,T.start(d,0n,b,[T.Binary{T.OwnedWord{a}}])) == T.Delivered{d,T.OwnedWord{U32.add(U32.mul(a,31),b)}} : T.Run}
law frame_captures:
  for d: U32
  for x: U32
  for f: U32
  for b: U32
  {T.run(2n,T.start(d,0n,x,[T.Unary{f,b}])) == T.Delivered{d,T.OwnedWord{U32.add(U32.mul(x,f),b)}} : T.Run}
law fuel_add:
  for n: Nat
  for m: Nat
  for r: T.Run
  {T.run(m,T.run(n,r)) == T.run(Nat.add(n,m),r) : T.Run}
