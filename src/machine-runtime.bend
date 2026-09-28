import Base
import ./machine-code.bend as A

# Internal function indices: alloc 0, Nat build/count 1/2, String reverse,
# append, equality and length 3..6, decimal rendering 7, primitives 8, run 9.
# Every cell is immutable after construction. Address zero is a shared tag-zero
# cell. The instance arena occupies [22 MiB,64 MiB); stacks are disjoint.
def allocator() -> List<&2,U32>:
  A.function(1,A.seq([
    A.guard(A.seq([A.get(0),A.i32(67108864),[35,0,107,75]])),
    [35,0],A.tee(2),A.get(0),[106,36,0],A.get(2)]))

def natural() -> List<&2,U32>:
  A.function(2,A.seq([
    A.guard(A.seq([A.get(0),A.i32(1048576),[75]])),
    [2,64,3,64],A.get(0),[69],A.branch(1),
    A.invoke(0,A.i32(8),A.i32(0)),A.set(3),
    A.get(3),A.i32(1),A.store(0),A.get(3),A.get(2),A.store(4),
    A.get(3),A.set(2),A.get(0),A.i32(1),[107],A.set(0),A.jump(0),[11,11],A.get(2)]))

def count() -> List<&2,U32>:
  A.function(1,A.seq([
    [2,64,3,64],A.get(0),A.load(0),[69],A.branch(1),
    A.guard(A.seq([A.get(2),A.i32(1048576),[79]])),
    A.get(2),A.i32(1),[106],A.set(2),A.get(0),A.load(4),A.set(0),A.jump(0),[11,11],A.get(2)]))

def reverse() -> List<&2,U32>:
  A.function(2,A.seq([
    [2,64,3,64],A.get(0),A.load(0),[69],A.branch(1),
    A.guard(A.seq([A.get(3),A.i32(1048576),[79]])),
    A.get(3),A.i32(1),[106],A.set(3),
    A.invoke(0,A.i32(12),A.i32(0)),A.set(2),
    A.get(2),A.i32(1),A.store(0),A.get(2),A.get(0),A.load(4),A.store(4),
    A.get(2),A.get(1),A.store(8),A.get(2),A.set(1),
    A.get(0),A.load(8),A.set(0),A.jump(0),[11,11],A.get(1)]))

def append() -> List<&2,U32>:
  A.function(0,A.seq([
    A.guard(A.seq([A.invoke(6,A.get(0),A.i32(0)),A.invoke(6,A.get(1),A.i32(0)),[106],A.i32(1048576),[75]])),
    A.invoke(3,A.invoke(3,A.get(0),A.i32(0)),A.get(1))]))

def equal() -> List<&2,U32>:
  A.function(1,A.seq([
    [3,64],
    A.when(A.seq([A.get(0),A.load(0),[69]]),A.seq([A.get(1),A.load(0),[69,15]])),
    A.when(A.seq([A.get(1),A.load(0),[69]]),A.seq([A.i32(0),[15]])),
    A.when(A.seq([A.get(0),A.load(4),A.get(1),A.load(4),[71]]),A.seq([A.i32(0),[15]])),
    A.guard(A.seq([A.get(2),A.i32(1048576),[79]])),A.get(2),A.i32(1),[106],A.set(2),
    A.get(0),A.load(8),A.set(0),A.get(1),A.load(8),A.set(1),A.jump(0),[11],A.i32(0)]))

def length() -> List<&2,U32>:
  A.function(1,A.seq([
    [2,64,3,64],A.get(0),A.load(0),[69],A.branch(1),
    A.guard(A.seq([A.get(2),A.i32(1048576),[79]])),
    A.get(2),A.i32(1),[106],A.set(2),A.get(0),A.load(8),A.set(0),A.jump(0),[11,11],A.get(2)]))

def show() -> List<&2,U32>:
  A.function(2,A.seq([
    [2,64,3,64],A.invoke(0,A.i32(12),A.i32(0)),A.set(3),
    A.get(3),A.i32(1),A.store(0),
    A.get(3),A.get(0),A.i32(10),[112],A.i32(48),[106],A.store(4),
    A.get(3),A.get(2),A.store(8),A.get(3),A.set(2),
    A.get(0),A.i32(10),[110],A.tee(0),[69],A.branch(1),A.jump(0),[11,11],A.get(2)]))
