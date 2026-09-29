import Base
import ./primitive-op.bend as O

def name(op: O.Op) -> String:
  match op:
    case O.WAdd{}: "U32.add"
    case O.WSub{}: "U32.sub"
    case O.WMul{}: "U32.mul"
    case O.WDiv{}: "U32.div"
    case O.WRem{}: "U32.mod"
    case O.WNot{}: "U32.not"
    case O.WAnd{}: "U32.and"
    case O.WCmp{}: "U32.cmp"
    case O.WEq{}: "U32.is_eq"
    case O.WNe{}: "U32.is_ne"
    case O.WLt{}: "U32.is_lt"
    case O.WLe{}: "U32.is_le"
    case O.WGt{}: "U32.is_gt"
    case O.WGe{}: "U32.is_ge"
    case O.WShl{}: "U32.shln"
    case O.WShr{}: "U32.shrn"
    case O.ToNat{}: "U32.to_nat"
    case O.FromNat{}: "U32.from_nat"
    case O.FromCode{}: "Char.from_u32"
    case O.ToCode{}: "Char.to_u32"
    case O.CEq{}: "Char.is_eq"
    case O.CSpace{}: "Char.is_space"
    case O.NAdd{}: "Nat.add"
    case O.NSub{}: "Nat.sub"
    case O.NMul{}: "Nat.mul"
    case O.NCmp{}: "Nat.cmp"
    case O.NEq{}: "Nat.is_eq"
    case O.NNe{}: "Nat.is_ne"
    case O.NLt{}: "Nat.is_lt"
    case O.NLe{}: "Nat.is_le"
    case O.NGt{}: "Nat.is_gt"
    case O.NGe{}: "Nat.is_ge"
    case O.WShow{}: "U32.show"
    case O.NShow{}: "Nat.show"
    case O.SEq{}: "String.eq"
    case O.SAppend{}: "String.append"
    case O.SReverse{}: "String.reverse"
    case O.SLength{}: "String.length"
    case O.SEmpty{}: "String.is_empty"

def code(op: O.Op) -> U32:
  match op:
    case O.WAdd{}: 0
    case O.WSub{}: 1
    case O.WMul{}: 2
    case O.WDiv{}: 3
    case O.WRem{}: 4
    case O.WNot{}: 5
    case O.WAnd{}: 6
    case O.WCmp{}: 7
    case O.WEq{}: 8
    case O.WNe{}: 9
    case O.WLt{}: 10
    case O.WLe{}: 11
    case O.WGt{}: 12
    case O.WGe{}: 13
    case O.WShl{}: 14
    case O.WShr{}: 15
    case O.ToNat{}: 16
    case O.FromNat{}: 17
    case O.FromCode{}: 18
    case O.ToCode{}: 19
    case O.CEq{}: 20
    case O.CSpace{}: 21
    case O.NAdd{}: 22
    case O.NSub{}: 23
    case O.NMul{}: 24
    case O.NCmp{}: 25
    case O.NEq{}: 26
    case O.NNe{}: 27
    case O.NLt{}: 28
    case O.NLe{}: 29
    case O.NGt{}: 30
    case O.NGe{}: 31
    case O.WShow{}: 32
    case O.NShow{}: 33
    case O.SEq{}: 34
    case O.SAppend{}: 35
    case O.SReverse{}: 36
    case O.SLength{}: 37
    case O.SEmpty{}: 38

def all() -> List<&2,O.Op>:
  [O.WAdd{}, O.WSub{}, O.WMul{}, O.WDiv{}, O.WRem{}, O.WNot{}, O.WAnd{}, O.WCmp{}, O.WEq{}, O.WNe{}, O.WLt{}, O.WLe{}, O.WGt{}, O.WGe{}, O.WShl{}, O.WShr{}, O.ToNat{}, O.FromNat{}, O.FromCode{}, O.ToCode{}, O.CEq{}, O.CSpace{}, O.NAdd{}, O.NSub{}, O.NMul{}, O.NCmp{}, O.NEq{}, O.NNe{}, O.NLt{}, O.NLe{}, O.NGt{}, O.NGe{}, O.WShow{}, O.NShow{}, O.SEq{}, O.SAppend{}, O.SReverse{}, O.SLength{}, O.SEmpty{}]

def find(ops: List<&2,O.Op>, +text: String) -> Maybe<&2,O.Op>:
  match ops:
    case Nil{}: None{}
    case Con{+op,+tail}:
      Bool.pick(Maybe<&2,O.Op>,String.eq(name(op),text),Some{op},find(tail,text))

def lookup(text: String) -> Maybe<&2,O.Op>:
  find(all(),text)

def inputs(op: O.Op) -> List<&2,String>:
  match op:
    case O.WAdd{}: ["U32", "U32"]
    case O.WSub{}: ["U32", "U32"]
    case O.WMul{}: ["U32", "U32"]
    case O.WDiv{}: ["U32", "U32"]
    case O.WRem{}: ["U32", "U32"]
    case O.WNot{}: ["U32"]
    case O.WAnd{}: ["U32", "U32"]
    case O.WCmp{}: ["U32", "U32"]
    case O.WEq{}: ["U32", "U32"]
    case O.WNe{}: ["U32", "U32"]
    case O.WLt{}: ["U32", "U32"]
    case O.WLe{}: ["U32", "U32"]
    case O.WGt{}: ["U32", "U32"]
    case O.WGe{}: ["U32", "U32"]
    case O.WShl{}: ["U32", "Nat"]
    case O.WShr{}: ["U32", "Nat"]
    case O.ToNat{}: ["U32"]
    case O.FromNat{}: ["Nat"]
    case O.FromCode{}: ["U32"]
    case O.ToCode{}: ["Char"]
    case O.CEq{}: ["Char", "Char"]
    case O.CSpace{}: ["Char"]
    case O.NAdd{}: ["Nat", "Nat"]
    case O.NSub{}: ["Nat", "Nat"]
    case O.NMul{}: ["Nat", "Nat"]
    case O.NCmp{}: ["Nat", "Nat"]
    case O.NEq{}: ["Nat", "Nat"]
    case O.NNe{}: ["Nat", "Nat"]
    case O.NLt{}: ["Nat", "Nat"]
    case O.NLe{}: ["Nat", "Nat"]
    case O.NGt{}: ["Nat", "Nat"]
    case O.NGe{}: ["Nat", "Nat"]
    case O.WShow{}: ["U32"]
    case O.NShow{}: ["Nat"]
    case O.SEq{}: ["String", "String"]
    case O.SAppend{}: ["String", "String"]
    case O.SReverse{}: ["String"]
    case O.SLength{}: ["String"]
    case O.SEmpty{}: ["String"]

def quantities(op: O.Op) -> List<&2,U32>:
  match op:
    case O.WAdd{}: [1, 1]
    case O.WSub{}: [1, 1]
    case O.WMul{}: [1, 1]
    case O.WDiv{}: [1, 2]
    case O.WRem{}: [1, 2]
    case O.WNot{}: [1]
    case O.WAnd{}: [1, 1]
    case O.WCmp{}: [1, 1]
    case O.WEq{}: [1, 1]
    case O.WNe{}: [1, 1]
    case O.WLt{}: [1, 1]
    case O.WLe{}: [1, 1]
    case O.WGt{}: [1, 1]
    case O.WGe{}: [1, 1]
    case O.WShl{}: [1, 1]
    case O.WShr{}: [1, 1]
    case O.ToNat{}: [1]
    case O.FromNat{}: [1]
    case O.FromCode{}: [1]
    case O.ToCode{}: [1]
    case O.CEq{}: [1, 1]
    case O.CSpace{}: [1]
    case O.NAdd{}: [1, 1]
    case O.NSub{}: [1, 1]
    case O.NMul{}: [1, 2]
    case O.NCmp{}: [1, 1]
    case O.NEq{}: [1, 1]
    case O.NNe{}: [1, 1]
    case O.NLt{}: [1, 1]
    case O.NLe{}: [1, 1]
    case O.NGt{}: [1, 1]
    case O.NGe{}: [1, 1]
    case O.WShow{}: [1]
    case O.NShow{}: [1]
    case O.SEq{}: [1, 1]
    case O.SAppend{}: [1, 1]
    case O.SReverse{}: [1]
    case O.SLength{}: [1]
    case O.SEmpty{}: [1]

def output(op: O.Op) -> String:
  match op:
    case O.WAdd{}: "U32"
    case O.WSub{}: "U32"
    case O.WMul{}: "U32"
    case O.WDiv{}: "U32"
    case O.WRem{}: "U32"
    case O.WNot{}: "U32"
    case O.WAnd{}: "U32"
    case O.WCmp{}: "Cmp"
    case O.WEq{}: "Bool"
    case O.WNe{}: "Bool"
    case O.WLt{}: "Bool"
    case O.WLe{}: "Bool"
    case O.WGt{}: "Bool"
    case O.WGe{}: "Bool"
    case O.WShl{}: "U32"
    case O.WShr{}: "U32"
    case O.ToNat{}: "Nat"
    case O.FromNat{}: "U32"
    case O.FromCode{}: "Char"
    case O.ToCode{}: "U32"
    case O.CEq{}: "Bool"
    case O.CSpace{}: "Bool"
    case O.NAdd{}: "Nat"
    case O.NSub{}: "Nat"
    case O.NMul{}: "Nat"
    case O.NCmp{}: "Cmp"
    case O.NEq{}: "Bool"
    case O.NNe{}: "Bool"
    case O.NLt{}: "Bool"
    case O.NLe{}: "Bool"
    case O.NGt{}: "Bool"
    case O.NGe{}: "Bool"
    case O.WShow{}: "String"
    case O.NShow{}: "String"
    case O.SEq{}: "Bool"
    case O.SAppend{}: "String"
    case O.SReverse{}: "String"
    case O.SLength{}: "Nat"
    case O.SEmpty{}: "Bool"
