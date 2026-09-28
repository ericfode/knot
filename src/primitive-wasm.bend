import Base
import ./machine-code.bend as A
import ./primitive-op.bend as R
import ./primitive.bend as O

# The dispatcher consumes checked primitive arguments. U32 and Char are bits;
# Nat and String are cell addresses. Comparison results use Base's tag order.
def arm(op: R.Op, body: List<&2,U32>) -> List<&2,U32>:
  A.when(A.eq(A.get(0),A.i32(O.code(op))),A.seq([body,[15]]))

def compare(+a: U32, +b: U32) -> List<&2,U32>:
  A.select(A.binary(73,a,b),A.i32(0),A.select(A.binary(70,a,b),A.i32(1),A.i32(2)))

def divide(+rem: Bool) -> List<&2,U32>:
  A.select(A.eq(A.get(2),A.i32(0)),Bool.pick(List<&2,U32>,rem,A.get(1),A.i32(0)),A.binary(Bool.pick(U32,rem,112,110),1,2))

def shift(op: U32) -> List<&2,U32>:
  A.seq([A.invoke(2,A.get(2),A.i32(0)),A.set(3),
    A.select(A.seq([A.get(3),A.i32(32),[79]]),A.i32(0),A.binary(op,1,3))])

def counts(body: List<&2,U32>) -> List<&2,U32>:
  A.seq([A.invoke(2,A.get(1),A.i32(0)),A.set(3),A.invoke(2,A.get(2),A.i32(0)),A.set(4),body])

def nat(body: List<&2,U32>) -> List<&2,U32>:
  A.invoke(1,body,A.i32(0))

def bounded_mul() -> List<&2,U32>:
  A.seq([A.when(A.seq([A.get(4),[69,69]]),
    A.guard(A.seq([A.get(3),A.i32(1048576),A.get(4),[110,75]]))),nat(A.binary(108,3,4))])

def function() -> List<&2,U32>:
  A.function(2,A.seq([
    arm(R.WAdd{},A.binary(106,1,2)),arm(R.WSub{},A.binary(107,1,2)),arm(R.WMul{},A.binary(108,1,2)),
    arm(R.WDiv{},divide(False{})),arm(R.WRem{},divide(True{})),
    arm(R.WNot{},A.seq([A.get(1),A.i32(4294967295),[115]])),arm(R.WAnd{},A.binary(113,1,2)),
    arm(R.WCmp{},compare(1,2)),arm(R.WEq{},A.binary(70,1,2)),arm(R.WNe{},A.binary(71,1,2)),
    arm(R.WLt{},A.binary(73,1,2)),arm(R.WLe{},A.binary(77,1,2)),arm(R.WGt{},A.binary(75,1,2)),arm(R.WGe{},A.binary(79,1,2)),
    arm(R.WShl{},shift(116)),arm(R.WShr{},shift(118)),
    arm(R.ToNat{},nat(A.get(1))),arm(R.FromNat{},A.invoke(2,A.get(1),A.i32(0))),
    arm(R.FromCode{},A.get(1)),arm(R.ToCode{},A.get(1)),arm(R.CEq{},A.binary(70,1,2)),
    arm(R.CSpace{},A.seq([A.eq(A.get(1),A.i32(32)),A.get(1),A.i32(9),[79],A.get(1),A.i32(13),[77,113,114]])),
    arm(R.NAdd{},counts(nat(A.binary(106,3,4)))),
    arm(R.NSub{},counts(nat(A.select(A.binary(73,3,4),A.i32(0),A.binary(107,3,4))))),
    arm(R.NMul{},counts(bounded_mul())),arm(R.NCmp{},counts(compare(3,4))),
    arm(R.NEq{},counts(A.binary(70,3,4))),arm(R.NNe{},counts(A.binary(71,3,4))),arm(R.NLt{},counts(A.binary(73,3,4))),
    arm(R.NLe{},counts(A.binary(77,3,4))),arm(R.NGt{},counts(A.binary(75,3,4))),arm(R.NGe{},counts(A.binary(79,3,4))),
    arm(R.WShow{},A.invoke(7,A.get(1),A.i32(0))),arm(R.NShow{},A.invoke(7,A.invoke(2,A.get(1),A.i32(0)),A.i32(0))),
    arm(R.SEq{},A.invoke(5,A.get(1),A.get(2))),arm(R.SAppend{},A.invoke(4,A.get(1),A.get(2))),
    arm(R.SReverse{},A.invoke(3,A.get(1),A.i32(0))),arm(R.SLength{},nat(A.invoke(6,A.get(1),A.i32(0)))),
    arm(R.SEmpty{},A.seq([A.get(1),A.load(0),[69]])),
    A.i32(4294967295),A.load(0)]))
