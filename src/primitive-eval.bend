import Base
import ./syntax.bend as S
import ./primitive-op.bend as R

type Datum is Data:
  Bits{value: U32}
  Count{value: U32}
  Codes{values: List<&2,U32>}

def exhausted(-A: Type) -> Result<S.Error,A>:
  Fail{S.Exhausted{"primitive",S.At{0,0,0,0}}}

def bounded(+value: U32) -> Result<S.Error,Datum>:
  S.choose(Result<S.Error,Datum>,U32.is_le(value,1048576),u => Done{Count{value}},u => exhausted(Datum))

def boolean(value: Bool) -> Result<S.Error,Datum>:
  Done{Bits{Bool.pick(U32,value,1,0)}}

def compare(+a: U32, +b: U32) -> Result<S.Error,Datum>:
  Done{Bits{Bool.pick(U32,U32.is_lt(a,b),0,Bool.pick(U32,U32.is_eq(a,b),1,2))}}

# These guards state the source algebra; machine division and masked shifts
# are used only on their defined domains.
def div(+a: U32, +b: U32) -> U32:
  S.choose(U32,U32.is_eq(b,0),u => 0,u => U32.div(a,b))

def rem(+a: U32, +b: U32) -> U32:
  S.choose(U32,U32.is_eq(b,0),u => a,u => U32.mod(a,b))

def shl(+a: U32, +n: U32) -> U32:
  S.choose(U32,U32.is_ge(n,32),u => 0,u => U32.shln(a,U32.to_nat(n)))

def shr(+a: U32, +n: U32) -> U32:
  S.choose(U32,U32.is_ge(n,32),u => 0,u => U32.shrn(a,U32.to_nat(n)))

# Shown U32 text has at most ten codes; host recursion is safe here.
def code_list(text: String) -> List<&2,U32>:
  match text:
    case SNil{}: Nil{}
    case SCon{head,tail}: Con{Char.to_u32(head),code_list(tail)}

# Code lists reach 1048576 elements, so every traversal below is a tail call
# with an accumulator: the evaluator's lanes must not need host stack depth.
def count(codes: List<&2,U32>, +n: U32) -> U32:
  match codes:
    case Nil{}: n
    case Con{head,tail}: count(tail,U32.add(n,1))

# onto(a,b) is reverse(a) ++ b; reverse and append are its two uses.
def onto(codes: List<&2,U32>, acc: List<&2,U32>) -> List<&2,U32>:
  match codes:
    case Nil{}: acc
    case Con{head,tail}: onto(tail,Con{head,acc})

def equal(a: List<&2,U32>, b: List<&2,U32>, +same: Bool) -> Bool:
  match a b:
    case Con{x,xs} Con{y,ys}: equal(xs,ys,Bool.and(same,U32.is_eq(x,y)))
    case Nil{} Nil{}: same
    case _ _: False{}

def apply(op: R.Op, args: List<&2,Datum>) -> Result<S.Error,Datum>:
  match op args:
    case R.WAdd{} Con{Bits{a},Con{Bits{b},Nil{}}}: Done{Bits{U32.add(a,b)}}
    case R.WSub{} Con{Bits{a},Con{Bits{b},Nil{}}}: Done{Bits{U32.sub(a,b)}}
    case R.WMul{} Con{Bits{a},Con{Bits{b},Nil{}}}: Done{Bits{U32.mul(a,b)}}
    case R.WDiv{} Con{Bits{a},Con{Bits{b},Nil{}}}: Done{Bits{div(a,b)}}
    case R.WRem{} Con{Bits{a},Con{Bits{b},Nil{}}}: Done{Bits{rem(a,b)}}
    case R.WNot{} Con{Bits{a},Nil{}}: Done{Bits{U32.not(a)}}
    case R.WAnd{} Con{Bits{a},Con{Bits{b},Nil{}}}: Done{Bits{U32.and(a,b)}}
    case R.WCmp{} Con{Bits{a},Con{Bits{b},Nil{}}}: compare(a,b)
    case R.WEq{} Con{Bits{a},Con{Bits{b},Nil{}}}: boolean(U32.is_eq(a,b))
    case R.WNe{} Con{Bits{a},Con{Bits{b},Nil{}}}: boolean(U32.is_ne(a,b))
    case R.WLt{} Con{Bits{a},Con{Bits{b},Nil{}}}: boolean(U32.is_lt(a,b))
    case R.WLe{} Con{Bits{a},Con{Bits{b},Nil{}}}: boolean(U32.is_le(a,b))
    case R.WGt{} Con{Bits{a},Con{Bits{b},Nil{}}}: boolean(U32.is_gt(a,b))
    case R.WGe{} Con{Bits{a},Con{Bits{b},Nil{}}}: boolean(U32.is_ge(a,b))
    case R.WShl{} Con{Bits{a},Con{Count{n},Nil{}}}: Done{Bits{shl(a,n)}}
    case R.WShr{} Con{Bits{a},Con{Count{n},Nil{}}}: Done{Bits{shr(a,n)}}
    case R.ToNat{} Con{Bits{a},Nil{}}: bounded(a)
    case R.FromNat{} Con{Count{a},Nil{}}: Done{Bits{a}}
    case R.FromCode{} Con{Bits{a},Nil{}}: Done{Bits{a}}
    case R.ToCode{} Con{Bits{a},Nil{}}: Done{Bits{a}}
    case R.CEq{} Con{Bits{a},Con{Bits{b},Nil{}}}: boolean(U32.is_eq(a,b))
    case R.CSpace{} Con{Bits{+a},Nil{}}: boolean(Bool.or(U32.is_eq(a,32),Bool.and(U32.is_ge(a,9),U32.is_le(a,13))))
    case R.NAdd{} Con{Count{a},Con{Count{b},Nil{}}}: bounded(U32.add(a,b))
    case R.NSub{} Con{Count{+a},Con{Count{+b},Nil{}}}: bounded(Bool.pick(U32,U32.is_lt(a,b),0,U32.sub(a,b)))
    case R.NMul{} Con{Count{+a},Con{Count{+b},Nil{}}}:
      S.choose(Result<S.Error,Datum>,Bool.or(U32.is_eq(b,0),U32.is_le(a,div(1048576,b))),u => bounded(U32.mul(a,b)),u => exhausted(Datum))
    case R.NCmp{} Con{Count{a},Con{Count{b},Nil{}}}: compare(a,b)
    case R.NEq{} Con{Count{a},Con{Count{b},Nil{}}}: boolean(U32.is_eq(a,b))
    case R.NNe{} Con{Count{a},Con{Count{b},Nil{}}}: boolean(U32.is_ne(a,b))
    case R.NLt{} Con{Count{a},Con{Count{b},Nil{}}}: boolean(U32.is_lt(a,b))
    case R.NLe{} Con{Count{a},Con{Count{b},Nil{}}}: boolean(U32.is_le(a,b))
    case R.NGt{} Con{Count{a},Con{Count{b},Nil{}}}: boolean(U32.is_gt(a,b))
    case R.NGe{} Con{Count{a},Con{Count{b},Nil{}}}: boolean(U32.is_ge(a,b))
    case R.WShow{} Con{Bits{a},Nil{}}: Done{Codes{code_list(U32.show(a))}}
    case R.NShow{} Con{Count{a},Nil{}}: Done{Codes{code_list(U32.show(a))}}
    case R.SEq{} Con{Codes{a},Con{Codes{b},Nil{}}}: boolean(equal(a,b,True{}))
    case R.SAppend{} Con{Codes{+a},Con{Codes{+b},Nil{}}}:
      S.choose(Result<S.Error,Datum>,U32.is_le(U32.add(count(a,0),count(b,0)),1048576),u => Done{Codes{onto(onto(a,Nil{}),b)}},u => exhausted(Datum))
    case R.SReverse{} Con{Codes{a},Nil{}}: Done{Codes{onto(a,Nil{})}}
    case R.SLength{} Con{Codes{a},Nil{}}: bounded(count(a,0))
    case R.SEmpty{} Con{Codes{Nil{}},Nil{}}: boolean(True{})
    case R.SEmpty{} Con{Codes{Con{head,tail}},Nil{}}: boolean(False{})
    case _ _: Fail{S.Internal{"eval","primitive-arguments"}}
