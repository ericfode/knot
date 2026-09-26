import Base
import ./main.bend as V

# Test/proof fixtures only: drop successful unit results to compose known
# in-domain traces. Behavioral laws separately constrain fallible results.
def vector(-T: Data, pair: V.Vec<T> & Result<V.Error,Unit>) -> V.Vec<T>:
  (v,r) = pair
  v

def contents_pair(-T: Data, pair: V.Vec<T> & List<T>) -> List<T>:
  (v,xs) = pair
  xs

def contents(-T: Data, v: V.Vec<T>) -> List<T>:
  contents_pair(T,V.Vec.to_list(T,v))

def result(-T: Data, pair: V.Vec<T> & Result<V.Error,T>) -> Result<V.Error,T>:
  (v,r) = pair
  r

def unit_result(-T: Data, pair: V.Vec<T> & Result<V.Error,Unit>) -> Result<V.Error,Unit>:
  (v,r) = pair
  r

def slice_result(-T: Data, pair: V.Vec<T> & Result<V.Error,List<T>>) -> Result<V.Error,List<T>>:
  (v,r) = pair
  r

def metadata(-T: Data, pair: V.Vec<T> & U32) -> U32:
  (v,n) = pair
  n

def pop_contents(-T: Data, pair: V.Vec<T> & Result<V.Error,T>) -> List<T> & Result<V.Error,T>:
  (v,r) = pair
  (contents(T,v),r)

def unit_contents(-T: Data, pair: V.Vec<T> & Result<V.Error,Unit>) -> List<T> & Result<V.Error,Unit>:
  (v,r) = pair
  (contents(T,v),r)

def one(-T: Data, x: T) -> V.Vec<T>:
  vector(T,V.Vec.push(T,V.Vec.new(T),x))

def two(-T: Data, x: T, y: T) -> V.Vec<T>:
  vector(T,V.Vec.push(T,one(T,x),y))

def three(-T: Data, x: T, y: T, z: T) -> V.Vec<T>:
  vector(T,V.Vec.push(T,two(T,x,y),z))

def five(-T: Data, a: T, b: T, c: T, d: T, e: T) -> V.Vec<T>:
  vector(T,V.Vec.push(T,vector(T,V.Vec.push(T,three(T,a,b,c),d)),e))

def value_vector(-T: Data, pair: V.Vec<T> & Result<V.Error,T>) -> V.Vec<T>:
  (v,r) = pair
  v
