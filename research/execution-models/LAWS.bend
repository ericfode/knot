import Base
import ./model.bend as M

# Universal payloads over inhabited Data types; all five control states covered.
# No theorem below claims concurrent memory safety or allocator correctness.
law first_left:
  for -T: Data
  for x: T
  {M.left(T,M.JOpen{},x) == M.JAccept{M.JLeft{x}} : M.Update<T>}
law first_right:
  for -T: Data
  for x: T
  {M.right(T,M.JOpen{},x) == M.JAccept{M.JRight{x}} : M.Update<T>}
law finish_left:
  for -T: Data
  for a: T
  for b: T
  {M.left(T,M.JRight{b},a) == M.JAccept{M.JReady{a,b}} : M.Update<T>}
law finish_right:
  for -T: Data
  for a: T
  for b: T
  {M.right(T,M.JLeft{a},b) == M.JAccept{M.JReady{a,b}} : M.Update<T>}
law duplicate_left:
  for -T: Data
  for a: T
  for b: T
  {M.left(T,M.JLeft{a},b) == M.JReject{M.JLeft{a}} : M.Update<T>}
law duplicate_right:
  for -T: Data
  for a: T
  for b: T
  {M.right(T,M.JRight{a},b) == M.JReject{M.JRight{a}} : M.Update<T>}
law ready_left:
  for -T: Data
  for a: T
  for b: T
  for c: T
  {M.left(T,M.JReady{a,b},c) == M.JReject{M.JReady{a,b}} : M.Update<T>}
law ready_right:
  for -T: Data
  for a: T
  for b: T
  for c: T
  {M.right(T,M.JReady{a,b},c) == M.JReject{M.JReady{a,b}} : M.Update<T>}
law taken_left:
  for -T: Data
  for x: T
  {M.left(T,M.JTaken{},x) == M.JReject{M.JTaken{}} : M.Update<T>}
law taken_right:
  for -T: Data
  for x: T
  {M.right(T,M.JTaken{},x) == M.JReject{M.JTaken{}} : M.Update<T>}
law take_open:
  for -T: Data
  {M.take(T,M.JOpen{}) == M.JWait{M.JOpen{}} : M.Taken<T>}
law take_left:
  for -T: Data
  for x: T
  {M.take(T,M.JLeft{x}) == M.JWait{M.JLeft{x}} : M.Taken<T>}
law take_right:
  for -T: Data
  for x: T
  {M.take(T,M.JRight{x}) == M.JWait{M.JRight{x}} : M.Taken<T>}
law take_ready:
  for -T: Data
  for a: T
  for b: T
  {M.take(T,M.JReady{a,b}) == M.JYield{M.JTaken{},a,b} : M.Taken<T>}
law take_taken:
  for -T: Data
  {M.take(T,M.JTaken{}) == M.JDenied{M.JTaken{}} : M.Taken<T>}
law completion_order:
  for -T: Data
  for a: T
  for b: T
  {M.state(T,M.right(T,M.state(T,M.left(T,M.JOpen{},a)),b)) == M.state(T,M.left(T,M.state(T,M.right(T,M.JOpen{},b)),a)) : M.Join<T>}
law completed_payloads:
  for -T: Data
  for a: T
  for b: T
  {M.take(T,M.state(T,M.right(T,M.state(T,M.left(T,M.JOpen{},a)),b))) == M.JYield{M.JTaken{},a,b} : M.Taken<T>}
law second_take:
  for -T: Data
  for a: T
  for b: T
  {M.take(T,M.after_take(T,M.take(T,M.JReady{a,b}))) == M.JDenied{M.JTaken{}} : M.Taken<T>}
