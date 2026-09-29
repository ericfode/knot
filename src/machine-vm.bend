import Base
import ./machine-code.bend as A

# Fixed instruction words: [op,a,b,c,next]. Function metadata: [entry,slots,arity].
# Locals: pc=2, sp=3, bp=4, rp=5, op=6, instruction=7, a/b/c/next=8..11.
# Return records hold [next,bp,sp]. Operand frames reserve the source's lexical
# levels, then use a stack above those slots. Both stacks are bounded separately.
def push(value: List<&2,U32>) -> List<&2,U32>:
  A.seq([A.guard(A.seq([A.get(3),A.i32(23068668),[75]])),
    A.get(3),value,A.store(0),A.get(3),A.i32(4),[106],A.set(3)])

def pop(local: U32) -> List<&2,U32>:
  A.seq([A.get(3),A.i32(4),[107],A.tee(3),A.load(0),A.set(local)])

def arm(code: U32, body: List<&2,U32>) -> List<&2,U32>:
  A.when(A.eq(A.get(6),A.i32(code)),body)

def returning() -> List<&2,U32>:
  A.seq([pop(12),
    A.when(A.eq(A.get(5),A.i32(1048576)),A.seq([A.get(12),[15]])),
    A.get(5),A.i32(12),[107],A.set(5),
    A.get(5),A.load(0),A.set(2),A.get(5),A.load(4),A.set(4),A.get(5),A.load(8),A.set(3),
    push(A.get(12)),A.jump(1)])

def calling() -> List<&2,U32>:
  A.seq([
    A.get(8),A.i32(12),[108],A.i32(16),[106],A.set(12),
    A.get(3),A.get(12),A.load(8),A.i32(4),[108,107],A.set(16),
    A.guard(A.seq([A.get(5),A.i32(5242868),[75]])),
    A.get(5),A.get(11),A.store(0),A.get(5),A.get(4),A.store(4),A.get(5),A.get(16),A.store(8),
    A.get(5),A.i32(12),[106],A.set(5),A.get(16),A.set(4),
    A.get(16),A.get(12),A.load(4),A.i32(4),[108,106],A.set(3),
    A.guard(A.seq([A.get(3),A.i32(23068672),[75]])),
    A.get(12),A.load(0),A.set(2),A.jump(1)])

def construct() -> List<&2,U32>:
  A.seq([
    A.invoke(0,A.seq([A.get(9),A.i32(1),[106],A.i32(4),[108]]),A.i32(0)),A.set(13),
    A.get(13),A.get(8),A.store(0),
    A.get(3),A.get(9),A.i32(4),[108,107],A.set(3),A.i32(0),A.set(14),
    [2,64,3,64],A.get(14),A.get(9),[79],A.branch(1),
    A.get(13),A.get(14),A.i32(4),[108,106],
    A.get(3),A.get(14),A.i32(4),[108,106],A.load(0),A.store(4),
    A.get(14),A.i32(1),[106],A.set(14),A.jump(0),[11,11],push(A.get(13))])

def character() -> List<&2,U32>:
  A.seq([pop(12),A.invoke(0,A.i32(12),A.i32(0)),A.set(13),
    A.get(13),A.i32(1),A.store(0),A.get(13),A.get(8),A.store(4),A.get(13),A.get(12),A.store(8),push(A.get(13))])

def primitive() -> List<&2,U32>:
  A.seq([A.i32(0),A.set(13),A.when(A.eq(A.get(9),A.i32(2)),pop(13)),pop(12),
    push(A.seq([A.get(8),A.get(12),A.get(13),A.call(8)]))])

def function(code_base: U32) -> List<&2,U32>:
  A.function(15,A.seq([
    A.get(0),A.set(2),A.i32(5242880),A.set(4),A.i32(1048576),A.set(5),
    A.get(1),A.i32(4),[108],A.get(4),[106],A.set(3),
    [3,64],A.get(2),A.i32(20),[108],A.i32(code_base),[106],A.tee(7),A.load(0),A.set(6),
    A.get(7),A.load(4),A.set(8),A.get(7),A.load(8),A.set(9),A.get(7),A.load(12),A.set(10),A.get(7),A.load(16),A.set(11),
    arm(0,returning()),arm(1,push(A.get(8))),
    arm(2,push(A.seq([A.get(4),A.get(8),A.i32(4),[108,106],A.load(0)]))),
    arm(3,A.seq([pop(12),A.get(4),A.get(8),A.i32(4),[108,106],A.get(12),A.store(0)])),
    arm(4,calling()),arm(5,primitive()),arm(6,construct()),
    arm(7,A.seq([pop(12),push(A.seq([A.get(12),A.get(8),[106],A.load(0)]))])),
    arm(9,A.seq([pop(12),A.select(A.eq(A.get(12),A.get(8)),A.get(9),A.get(10)),A.set(2),A.jump(1)])),
    arm(10,character()),arm(11,push(A.invoke(1,A.get(8),A.i32(0)))),
    A.get(11),A.set(2),A.jump(0),[11],A.i32(0)]))
