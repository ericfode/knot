import Base
import ./syntax.bend as S
import ./core.bend as C
import ./opt-term.bend as T

def select(arms: List<&2,C.Term>, +tag: U32) -> Result<S.Error,C.Term>:
  match arms:
    case Nil{}: T.internal(C.Term,"missing-arm")
    case Con{+head,+tail}:
      match head:
        case C.Branch{pattern,fields,body}:
          S.choose(Result<S.Error,C.Term>,U32.is_eq(tag,pattern),u => Done{head},u => select(tail,tag))
        case _: T.internal(C.Term,"arm-node")

# Each constructor argument becomes one field binding, in declaration order.
# Erased fields remain erased; the removed cell has no observable identity.
def bind_fields(fields: List<&2,C.Binding>, args: List<&2,C.Term>, +body: C.Term) -> Result<S.Error,C.Term>:
  match fields args:
    case Nil{} Nil{}: Done{body}
    case Con{C.Binding{+token,+level,+q,+typ,param,known},tail} Con{+value,rest}:
      S.bind(C.Term,C.Term,bind_fields(tail,rest,body),next => Done{C.Let{token,level,q,typ,value,next}})
    case _ _: T.internal(C.Term,"field-arity")

def branch_args(branch: C.Term, args: List<&2,C.Term>) -> Result<S.Error,C.Term>:
  match branch:
    case C.Branch{tag,fields,body}: bind_fields(fields,args,body)
    case _: T.internal(C.Term,"arm-node")

def constant(value: C.Term, +arms: List<&2,C.Term>) -> Result<S.Error,Maybe<&2,C.Term>>:
  match value:
    case C.Value{token,typ,tag}:
      S.bind(C.Term,Maybe<&2,C.Term>,select(arms,tag),branch =>
        S.bind(C.Term,Maybe<&2,C.Term>,branch_args(branch,Nil{}),body => Done{Some{body}}))
    case C.Construct{token,typ,tag,fields,+args}:
      S.bind(C.Term,Maybe<&2,C.Term>,select(arms,tag),branch =>
        S.bind(C.Term,Maybe<&2,C.Term>,branch_args(branch,args),body => Done{Some{body}}))
    case _: Done{None{}}

# Fusion transfers the sole matched constructor to its fields. General
# constructor propagation would duplicate affine arguments or their evaluation.
def field_floor(fields: List<&2,C.Binding>) -> U32:
  match fields:
    case Nil{}: 4096
    case Con{C.Binding{token,level,q,typ,param,known},tail}: U32.min(level,field_floor(tail))

def without_parent(depth: Nat, level: U32, option: Maybe<&2,C.Term>) -> Result<S.Error,Maybe<&2,C.Term>>:
  match option:
    case None{}: Done{None{}}
    case Some{+term}:
      S.bind(U32,Maybe<&2,C.Term>,T.measure(depth,term,T.Uses{level}),uses =>
        Done{S.choose(Maybe<&2,C.Term>,U32.is_eq(uses,0),u => Some{term},u => None{})})

def fused_branch(depth: Nat, branch: C.Term, +args: List<&2,C.Term>) -> Result<S.Error,Maybe<&2,C.Term>>:
  match branch:
    case C.Branch{tag,+fields,+body}:
      S.bind(U32,Maybe<&2,C.Term>,T.measure(depth,C.Sequence{args},T.Ceiling{}),ceiling =>
        S.choose(Result<S.Error,Maybe<&2,C.Term>>,U32.is_le(ceiling,field_floor(fields)),u =>
          S.bind(C.Term,Maybe<&2,C.Term>,bind_fields(fields,args,body),term => Done{Some{term}}),u => Done{None{}}))
    case _: T.internal(Maybe<&2,C.Term>,"arm-node")

def fused_value(+depth: Nat, +level: U32, value: C.Term, arms: List<&2,C.Term>) -> Result<S.Error,Maybe<&2,C.Term>>:
  match value:
    case C.Value{token,typ,tag}:
      S.bind(Maybe<&2,C.Term>,Maybe<&2,C.Term>,constant(C.Value{token,typ,tag},arms),option => without_parent(depth,level,option))
    case C.Construct{token,typ,tag,fields,+args}:
      S.bind(C.Term,Maybe<&2,C.Term>,select(arms,tag),branch =>
        S.bind(Maybe<&2,C.Term>,Maybe<&2,C.Term>,fused_branch(depth,branch,args),option => without_parent(depth,level,option)))
    case _: Done{None{}}

def fuse(+depth: Nat, +level: U32, +value: C.Term, body: C.Term) -> Result<S.Error,Maybe<&2,C.Term>>:
  match body:
    case C.Case{token,id,typ,+arms}:
      S.choose(Result<S.Error,Maybe<&2,C.Term>>,U32.is_eq(level,id),u => fused_value(depth,level,value,arms),u => Done{None{}})
    case _: Done{None{}}

def literal(value: C.Term) -> Maybe<&2,C.Term>:
  match value:
    case C.Value{token,typ,tag}: Some{C.Value{token,typ,tag}}
    case _: None{}

def known(env: List<&2,C.Binding>, +level: U32) -> Maybe<&2,C.Term>:
  match env:
    case Nil{}: None{}
    case Con{C.Binding{token,id,q,typ,param,+value},+tail}:
      S.choose(Maybe<&2,C.Term>,U32.is_eq(id,level),u => value,u => known(tail,level))

def discardable(+quantity: U32) -> Bool:
  Bool.or(U32.is_eq(quantity,0),U32.is_eq(quantity,2))

# All currently verified core expressions are pure and terminating. Retain
# affine lets; Data/erased lets may disappear only when their level is unused.
def dead(depth: Nat, +token: S.Token, +level: U32, +quantity: U32, +typ: U32, +value: C.Term, +body: C.Term) -> Result<S.Error,C.Term>:
  S.bind(U32,C.Term,T.measure(depth,body,T.Uses{level}),uses =>
    S.choose(Result<S.Error,C.Term>,Bool.and(discardable(quantity),U32.is_eq(uses,0)),u => Done{body},u => Done{C.Let{token,level,quantity,typ,value,body}}))
