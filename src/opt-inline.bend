import Base
import ./syntax.bend as S
import ./core.bend as C
import ./opt-term.bend as T

def function_at(functions: List<&2,C.Function>, +index: U32) -> Maybe<&2,C.Function>:
  match functions:
    case Nil{}: None{}
    case Con{+head,+tail}:
      S.choose(Maybe<&2,C.Function>,U32.is_eq(index,0),u => Some{head},u => function_at(tail,U32.sub(index,1)))

# Parameters occupy [0,arity). A fresh translation relocates the entire
# callee, then these lets evaluate actuals once in the unchanged caller scope.
def arguments(params: List<&2,C.Parameter>, args: List<&2,C.Term>, +level: U32, +body: C.Term) -> Result<S.Error,C.Term>:
  match params args:
    case Nil{} Nil{}: Done{body}
    case Con{C.Parameter{+token,+q,+typ},tail} Con{+value,rest}:
      S.bind(C.Term,C.Term,arguments(tail,rest,U32.add(level,1),body),next => Done{C.Let{token,level,q,typ,value,next}})
    case _ _: T.internal(C.Term,"inline-arity")

def instantiate(depth: Nat, params: List<&2,C.Parameter>, args: List<&2,C.Term>, +body: C.Term, +base: U32) -> Result<S.Error,C.Term>:
  S.bind(C.Term,C.Term,T.shift(depth,body,base),moved => arguments(params,args,base,moved))

def candidate(+depth: Nat, function: Maybe<&2,C.Function>, +index: U32, +current: U32, +base: U32, +args: List<&2,C.Term>) -> Result<S.Error,Maybe<&2,C.Term>>:
  match function:
    case None{}: Done{None{}}
    case Some{C.Function{C.Signature{token,+params,result},+body}}:
      S.bind(U32,Maybe<&2,C.Term>,T.measure(depth,body,T.Calls{current}),recursive =>
      S.choose(Result<S.Error,Maybe<&2,C.Term>>,U32.is_eq(recursive,0),u =>
      S.bind(U32,Maybe<&2,C.Term>,T.measure(depth,C.Sequence{args},T.Ceiling{}),ceiling =>
      +fresh = T.maximum(base,ceiling)
      S.bind(U32,Maybe<&2,C.Term>,T.measure(depth,body,T.Size{}),size =>
        S.choose(Result<S.Error,Maybe<&2,C.Term>>,U32.is_le(size,32),u =>
          S.bind(U32,Maybe<&2,C.Term>,T.measure(depth,body,T.Calls{index}),calls =>
            S.choose(Result<S.Error,Maybe<&2,C.Term>>,U32.is_eq(calls,0),u =>
              S.bind(U32,Maybe<&2,C.Term>,T.measure(depth,body,T.Ceiling{}),ceiling =>
                S.choose(Result<S.Error,Maybe<&2,C.Term>>,U32.is_le(U32.add(fresh,T.maximum(ceiling,U32.from_nat(List.length(&2,C.Parameter,params)))),4096),u =>
                  S.bind(C.Term,Maybe<&2,C.Term>,instantiate(depth,params,args,body,fresh),term => Done{Some{term}}),u => Done{None{}})),u => Done{None{}})),u => Done{None{}}))),u => Done{None{}}))
