import Base
import ./main.bend as V
import ./observations.bend as O

# Universal over arbitrary Data elements; vector shapes/indices are fixed.
# These are substantive finite-shape refinement theorems, not a proof for all
# reachable lengths, capacities, or arbitrary operation traces.
law empty_contents:
  for -T: Data
  {O.contents(T,V.Vec.new(T)) == Nil{} : List<T>}

law singleton_get:
  for -T: Data
  for x: T
  {O.result(T,V.Vec.get(T,O.one(T,x),0)) == Done{x} : Result<V.Error,T>}

law growth_order:
  for -T: Data
  for a: T
  for b: T
  for c: T
  for d: T
  for e: T
  {O.contents(T,O.five(T,a,b,c,d,e)) == [a,b,c,d,e] : List<T>}

law reserve_preserves:
  for -T: Data
  for a: T
  for b: T
  for c: T
  {O.unit_contents(T,V.Vec.reserve(T,O.three(T,a,b,c),17)) == ([a,b,c],Done{Unit{}}) : List<T> & Result<V.Error,Unit>}

law set_preserves:
  for -T: Data
  for a: T
  for b: T
  for c: T
  for x: T
  {O.unit_contents(T,V.Vec.set(T,O.three(T,a,b,c),1,x)) == ([a,x,c],Done{Unit{}}) : List<T> & Result<V.Error,Unit>}

law swap_old_and_preserves:
  for -T: Data
  for a: T
  for b: T
  for c: T
  for x: T
  {O.pop_contents(T,V.Vec.swap(T,O.three(T,a,b,c),1,x)) == ([a,x,c],Done{b}) : List<T> & Result<V.Error,T>}

law push_pop_growth:
  for -T: Data
  for a: T
  for b: T
  for x: T
  {O.pop_contents(T,V.Vec.pop(T,O.three(T,a,b,x))) == ([a,b],Done{x}) : List<T> & Result<V.Error,T>}

law slice_order:
  for -T: Data
  for a: T
  for b: T
  for c: T
  for d: T
  for e: T
  {O.slice_result(T,V.Vec.slice(T,O.five(T,a,b,c,d,e),1,4)) == Done{[b,c,d]} : Result<V.Error,List<T>>}

law logical_bounds:
  for -T: Data
  for a: T
  for b: T
  for c: T
  for x: T
  {O.unit_contents(T,V.Vec.set(T,O.three(T,a,b,c),3,x)) == ([a,b,c],Fail{V.Bounds{}}) : List<T> & Result<V.Error,Unit>}

law max_index:
  for -T: Data
  for a: T
  {O.result(T,V.Vec.get(T,O.one(T,a),4294967295)) == Fail{V.Bounds{}} : Result<V.Error,T>}

law zero_limit:
  for -T: Data
  for x: T
  {O.unit_contents(T,V.Vec.push(T,V.Vec.bounded(T,0),x)) == (Nil{},Fail{V.Limit{}}) : List<T> & Result<V.Error,Unit>}

law empty_pop:
  for -T: Data
  {O.pop_contents(T,V.Vec.pop(T,V.Vec.new(T))) == (Nil{},Fail{V.Empty{}}) : List<T> & Result<V.Error,T>}

law empty_slice:
  for -T: Data
  {O.slice_result(T,V.Vec.slice(T,V.Vec.new(T),0,0)) == Done{Nil{}} : Result<V.Error,List<T>>}

law reversed_slice:
  for -T: Data
  for x: T
  {O.slice_result(T,V.Vec.slice(T,O.one(T,x),1,0)) == Fail{V.InvalidRange{}} : Result<V.Error,List<T>>}

law maximum_reserve:
  for -T: Data
  for x: T
  {O.unit_contents(T,V.Vec.reserve(T,O.one(T,x),4294967295)) == ([x],Fail{V.Limit{}}) : List<T> & Result<V.Error,Unit>}

# Concrete metadata normalizations, distinct from the element-parametric laws.
law initial_metadata:
  {O.metadata(U32,V.Vec.length(U32,V.Vec.new(U32))) == 0 : U32}
law initial_capacity:
  {O.metadata(U32,V.Vec.capacity(U32,V.Vec.new(U32))) == 1 : U32}
law rounded_capacity:
  {O.metadata(U32,V.Vec.capacity(U32,O.vector(U32,V.Vec.reserve(U32,V.Vec.new(U32),17)))) == 32 : U32}
law effective_limit:
  {O.metadata(U32,V.Vec.limit(U32,V.Vec.bounded(U32,4294967295))) == 16777216 : U32}

law get_preserves:
  for -T: Data
  for a: T
  for b: T
  for c: T
  {O.pop_contents(T,V.Vec.get(T,O.three(T,a,b,c),1)) == ([a,b,c],Done{b}) : List<T> & Result<V.Error,T>}

law set_then_get:
  for -T: Data
  for a: T
  for b: T
  for c: T
  for x: T
  {O.result(T,V.Vec.get(T,O.vector(T,V.Vec.set(T,O.three(T,a,b,c),1,x)),1)) == Done{x} : Result<V.Error,T>}

law push_success:
  for -T: Data
  for a: T
  for b: T
  for x: T
  {O.unit_contents(T,V.Vec.push(T,O.two(T,a,b),x)) == ([a,b,x],Done{Unit{}}) : List<T> & Result<V.Error,Unit>}

# Necessary state observation: contents alone cannot see an empty trailing slot.
law pop_length:
  for -T: Data
  for a: T
  for b: T
  for x: T
  {O.metadata(T,V.Vec.length(T,O.value_vector(T,V.Vec.pop(T,O.three(T,a,b,x))))) == 2 : U32}

# Arithmetic-only ceiling witness: no 2^24-slot allocation is needed to check it.
law maximum_plan:
  {V.plan_step(24n,1,0n,16777216,False{}) == (16777216,24n) : U32 & Nat}
law exact_limit_reserve:
  {O.unit_result(U32,V.Vec.reserve(U32,V.Vec.bounded(U32,3),3)) == Done{Unit{}} : Result<V.Error,Unit>}
